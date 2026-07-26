"""KEF retrieval gateway — single path for Investigation Skill evidence."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.isf.evidence import EvidenceRef, EvidenceType, document_ref_count
from cobra_core.kef.audit import KEF_AUDIT, KefAuditLog
from cobra_core.kef.citation import assign_citation_labels
from cobra_core.kef.config import KefConfig, kef_enabled, load_kef_config
from cobra_core.kef.deduplication import deduplicate
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.filters import missing_skill_types
from cobra_core.kef.metrics import KEF_METRICS, KefMetrics
from cobra_core.kef.ranking import rank_items
from cobra_core.kef.registry import CONNECTOR_REGISTRY, ConnectorRegistry
from cobra_core.kef.resolver import resolve_refs
from cobra_core.kef.security import Principal, filter_permitted
from cobra_core.kef.types import (
    RetrievalMode,
    RetrievalQuery,
    RetrievalResult,
)


class KefGateway:
    """
    Knowledge & Evidence Framework entrypoint.

    ISF calls this before AIR. Computer never bypasses KEF for evidence bodies.
    """

    def __init__(
        self,
        *,
        registry: ConnectorRegistry | None = None,
        config: KefConfig | None = None,
        audit: KefAuditLog | None = None,
        metrics: KefMetrics | None = None,
    ) -> None:
        self.registry = registry if registry is not None else CONNECTOR_REGISTRY
        self.config = config or load_kef_config()
        self.audit = audit if audit is not None else KEF_AUDIT
        self.metrics = metrics if metrics is not None else KEF_METRICS

    def retrieve_for_skill(
        self,
        *,
        skill_id: str,
        required_evidence: frozenset[EvidenceType],
        optional_evidence: frozenset[EvidenceType] | None = None,
        evidence_refs: list[EvidenceRef] | tuple[EvidenceRef, ...] = (),
        correlation_id: str = "",
        principal: Principal | None = None,
        mode: RetrievalMode = RetrievalMode.EXACT,
        metadata_filters: dict[str, Any] | None = None,
        max_results: int | None = None,
    ) -> RetrievalResult:
        t0 = time.perf_counter()
        if not self.config.enabled or not kef_enabled():
            raise KefError(KefErrorCode.KEF_DISABLED, "KEF_ENABLED=false")

        if mode == RetrievalMode.SEMANTIC and not self.config.semantic_enabled:
            raise KefError(
                KefErrorCode.INVALID_REQUEST,
                "semantic search is disabled (out of scope for KC-027)",
            )

        principal = principal or Principal()
        required_types = frozenset(t.value for t in required_evidence)
        optional_types = frozenset(t.value for t in (optional_evidence or frozenset()))
        limit = max_results or self.config.max_results

        query = RetrievalQuery(
            mode=mode,
            skill_id=skill_id,
            correlation_id=correlation_id,
            ref_ids=tuple(r.ref_id for r in evidence_refs),
            required_skill_types=required_types,
            optional_skill_types=optional_types,
            metadata_filters=dict(metadata_filters or {}),
            max_results=limit,
            actor_role=principal.role,
            org_id=principal.org_id,
            classification_ceiling=principal.classification_ceiling,
        )

        # 1) Resolve request refs through connectors (+ optional seed)
        items = resolve_refs(evidence_refs, registry=self.registry, config=self.config)

        # 2) Optional connector search for registry/metadata/hybrid modes
        connector_ids: list[str] = []
        if mode in {RetrievalMode.METADATA, RetrievalMode.HYBRID, RetrievalMode.REGISTRY}:
            for conn in self.registry.all():
                cid = getattr(conn, "connector_id", "unknown")
                if cid == "evidence_vault":
                    continue
                try:
                    found = conn.search(query)
                except KefError:
                    continue
                connector_ids.append(cid)
                items.extend(found)
        else:
            # Exact: still record which connectors held the refs
            for ref in evidence_refs:
                for conn in self.registry.all():
                    cid = getattr(conn, "connector_id", "")
                    if cid == "evidence_vault":
                        continue
                    try:
                        if conn.lookup(ref.ref_id) is not None and cid not in connector_ids:
                            connector_ids.append(cid)
                    except KefError:
                        continue
            if not connector_ids:
                connector_ids = ["memory"]

        # 3) Permissions
        allowed, denied = filter_permitted(items, principal)

        # 4) Deduplicate
        unique, dup_removed, _rels = deduplicate(allowed)

        # 5) Rank + cap
        ranked = rank_items(unique, query)[:limit]

        # 6) Required evidence validation (+ document_comparison cardinality)
        missing = missing_skill_types(ranked, required_types)
        if skill_id == "document_comparison" and document_ref_count(evidence_refs) < 2:
            if EvidenceType.DOCUMENT_PAIR.value not in missing:
                missing.append(EvidenceType.DOCUMENT_PAIR.value)
            missing = sorted(set(missing))

        # Integrity gate (optional)
        if self.config.require_integrity_hash:
            for item in ranked:
                if not item.integrity_hash:
                    missing.append("integrity:" + item.id)

        citations = assign_citation_labels(ranked) if not missing else []
        latency_ms = int((time.perf_counter() - t0) * 1000)
        status = "missing_required" if missing else "ok"
        result_label = "missing_required" if missing else "success"
        if denied and not ranked and not missing:
            result_label = "permission_denied"
            status = "permission_denied"

        audit_entry = self.audit.record(
            {
                "correlation_id": correlation_id,
                "skill_id": skill_id,
                "connector": connector_ids[0] if len(connector_ids) == 1 else "multi",
                "connectors": connector_ids,
                "query_type": mode.value,
                "filters": {
                    "required": sorted(required_types),
                    "optional": sorted(optional_types),
                    "metadata_keys": sorted((metadata_filters or {}).keys()),
                },
                "returned_count": len(ranked),
                "duplicates_removed": dup_removed,
                "ranking_top_ids": [i.id for i in ranked[:10]],
                "citations_produced": [c.public_id() for c in citations],
                "permission_failures": len(denied),
                "missing_required": missing,
                "status": status,
                "latency_ms": latency_ms,
            }
        )

        self.metrics.record_retrieval(
            skill_id=skill_id,
            connector=connector_ids[0] if len(connector_ids) == 1 else "multi",
            mode=mode.value,
            result=result_label,
            returned_count=len(ranked),
            duplicates_removed=dup_removed,
            permission_denials=len(denied),
            citations=len(citations),
            missing_required=bool(missing),
            latency_ms=latency_ms,
            is_lookup=mode == RetrievalMode.EXACT,
        )

        return RetrievalResult(
            items=ranked,
            citations=citations,
            missing_required=missing,
            duplicates_removed=dup_removed,
            permission_denials=len(denied),
            connector_ids=connector_ids,
            mode=mode,
            latency_ms=latency_ms,
            audit_id=str(audit_entry.get("audit_id") or ""),
        )


# Process-wide gateway (tests may construct isolated instances)
KEF_GATEWAY = KefGateway()
