"""Resolve Computer/ISF evidence refs through connectors into EvidenceItems."""

from __future__ import annotations

from cobra_core.isf.evidence import EvidenceRef
from cobra_core.kef.config import KefConfig
from cobra_core.kef.connectors.memory import MemoryConnector
from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.normalizer import normalize_evidence_ref
from cobra_core.kef.registry import ConnectorRegistry
from cobra_core.kef.types import EvidenceItem


def resolve_refs(
    refs: list[EvidenceRef] | tuple[EvidenceRef, ...],
    *,
    registry: ConnectorRegistry,
    config: KefConfig,
) -> list[EvidenceItem]:
    """
    Resolve opaque evidence handles.

    Lookup order: all connectors by ref_id, then optional request-seed into memory.
    """
    resolved: list[EvidenceItem] = []
    seen: set[str] = set()

    for ref in refs:
        item = _lookup_across(registry, ref.ref_id)
        if item is None and config.allow_request_seed:
            item = normalize_evidence_ref(ref, source="request", connector_id="memory")
            try:
                memory = registry.get("memory")
            except KefError:
                memory = None
            if isinstance(memory, MemoryConnector):
                memory.upsert(item)
        if item is None:
            # Leave gap — missing type validation happens later
            continue
        # Prefer skill type from the request ref when connector item lacks it
        if item.skill_evidence_type is None:
            from dataclasses import replace

            item = replace(item, skill_evidence_type=ref.evidence_type.value)
        if item.id not in seen:
            seen.add(item.id)
            resolved.append(item)
    return resolved


def _lookup_across(registry: ConnectorRegistry, ref_id: str) -> EvidenceItem | None:
    for conn in registry.all():
        if getattr(conn, "connector_id", "") == "evidence_vault":
            # Stub — skip hard failures during multi-connector resolve
            continue
        try:
            found = conn.lookup(ref_id)
        except KefError as exc:
            if exc.code in {
                KefErrorCode.CONNECTOR_UNAVAILABLE,
                KefErrorCode.NOT_IMPLEMENTED,
            }:
                continue
            raise
        if found is not None:
            return found
    return None
