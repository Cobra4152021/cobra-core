"""
Computer → ISF wire adapter (Protocol V1 compatible).

Computer submits skill_id (+ optional version), evidence refs, task inputs,
and request profile. Provider/model/OpenAI fields are rejected.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from cobra_core.isf.enabled import isf_enabled
from cobra_core.isf.engine import SkillEngine
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import EvidenceRef, EvidenceType, parse_evidence_type
from cobra_core.isf.types import SkillExecutionStatus, SkillRequest, SkillResult
from cobra_core.isf.versioning import assert_version_compatible

# Fields Computer must never send (provider selection belongs to AIR).
_FORBIDDEN_KEYS = frozenset(
    {
        "provider_id",
        "provider",
        "model_id",
        "model",
        "openai_api_key",
        "openai_base_url",
        "openai_model",
        "max_completion_tokens",
        "air_route",
        "routing_instructions",
        "capabilities",  # raw AIR capability arrays — skills expand these
        "preferred_provider",
        "preferred_model",
    }
)


def _reject_provider_fields(payload: dict[str, Any]) -> None:
    bad = sorted(k for k in payload if k in _FORBIDDEN_KEYS)
    # Nested metadata may carry the same forbidden keys.
    meta = payload.get("metadata")
    if isinstance(meta, dict):
        bad.extend(sorted(f"metadata.{k}" for k in meta if k in _FORBIDDEN_KEYS))
    if bad:
        raise IsfError(
            IsfErrorCode.MANIFEST_INVALID,
            "Computer must request skills, not providers/models/capabilities: "
            + ", ".join(bad[:8]),
        )


def map_evidence_refs(raw: Any) -> tuple[EvidenceRef, ...]:
    """Map Protocol / Computer evidence references into typed ISF evidence."""
    if raw is None:
        return ()
    if not isinstance(raw, list):
        raise IsfError(
            IsfErrorCode.MANIFEST_INVALID,
            "evidence must be a list of references",
        )
    out: list[EvidenceRef] = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                f"evidence[{i}] must be an object",
            )
        et_raw = item.get("evidence_type") or item.get("type") or item.get("kind")
        if not et_raw:
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                f"evidence[{i}] missing evidence_type",
            )
        try:
            et = parse_evidence_type(str(et_raw))
        except ValueError as exc:
            raise IsfError(IsfErrorCode.MANIFEST_INVALID, str(exc)[:160]) from exc
        ref_id = str(item.get("ref_id") or item.get("id") or item.get("reference") or "").strip()
        if not ref_id:
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                f"evidence[{i}] missing ref_id",
            )
        raw_meta = item.get("metadata")
        meta_in: dict[str, Any] = raw_meta if isinstance(raw_meta, dict) else {}
        # Bound metadata — never store evidence body text.
        meta: dict[str, Any] = {}
        if "document_count" in meta_in:
            try:
                meta["document_count"] = int(meta_in["document_count"])
            except (TypeError, ValueError):
                meta["document_count"] = 1
        if item.get("content_hash"):
            meta["content_hash"] = str(item["content_hash"])[:64]
        elif item.get("text"):
            # Hash only — never retain raw text in the ref.
            digest = hashlib.sha256(
                str(item["text"]).encode("utf-8", errors="replace")
            ).hexdigest()[:16]
            meta["content_hash"] = digest
        out.append(EvidenceRef(evidence_type=et, ref_id=ref_id, metadata=meta))
    return tuple(out)


def skill_request_from_computer(
    payload: dict[str, Any],
    *,
    correlation_id: str = "",
) -> SkillRequest:
    """Accept a Protocol V1 / Computer skill request body."""
    _reject_provider_fields(payload)
    skill_id = str(payload.get("skill_id") or payload.get("skill") or "").strip()
    if not skill_id:
        raise IsfError(IsfErrorCode.MANIFEST_INVALID, "skill_id is required")
    skill_version = payload.get("skill_version") or payload.get("version")
    if skill_version is not None:
        skill_version = str(skill_version).strip() or None
    evidence = map_evidence_refs(payload.get("evidence") or payload.get("evidence_refs"))
    profile = (
        str(
            payload.get("profile_id")
            or payload.get("profile")
            or payload.get("request_profile")
            or "default"
        )
        .strip()
        .lower()
    )
    corr = (
        correlation_id
        or str(payload.get("correlation_id") or "").strip()
        or str(payload.get("request_id") or "").strip()
    )
    task = str(payload.get("task") or payload.get("task_input") or "investigation").strip()
    inputs = payload.get("inputs") if isinstance(payload.get("inputs"), dict) else {}
    meta: dict[str, Any] = {}
    if isinstance(payload.get("metadata"), dict):
        # Strip forbidden keys again for safety.
        meta = {
            k: v
            for k, v in payload["metadata"].items()
            if k not in _FORBIDDEN_KEYS and k not in {"prompt", "messages", "api_key"}
        }
    if inputs:
        meta["task_inputs"] = {
            k: (str(v)[:200] if not isinstance(v, (int, float, bool)) else v)
            for k, v in list(inputs.items())[:20]
        }
    return SkillRequest(
        skill_id=skill_id,
        skill_version=skill_version,
        evidence=evidence,
        profile_id=profile,
        correlation_id=corr,
        task=task,
        metadata=meta,
    )


def proposal_from_skill_result(result: SkillResult) -> dict[str, Any]:
    """
    Map ISF result → Protocol V1-compatible proposal envelope.

    Additive metadata only — pending_approval for human gate.
    """
    if result.status in {
        SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE,
        SkillExecutionStatus.FAILED,
        SkillExecutionStatus.STRUCTURED_OUTPUT_INVALID,
    }:
        proposal_status = "failed"
    else:
        # Successful structured results always require human approval.
        proposal_status = "pending_approval"

    return {
        "ok": proposal_status == "pending_approval",
        "proposal": {
            "status": proposal_status,
            "skill_id": result.skill_id,
            "skill_version": result.skill_version,
            "structured_result": result.output,
            "confidence": result.confidence,
            "needs_human_review": result.needs_human_review,
            "missing_information": list((result.output or {}).get("missing_information") or [])
            if isinstance(result.output, dict)
            else [],
            "correlation_id": result.correlation_id or None,
            "selected_provider": result.selected_provider,
            "selected_model": result.selected_model,
            "route_reason": result.route_reason,
            "execution_status": result.status.value,
            "human_approval_required": True,
            "created_at_ms": int(time.time() * 1000),
        },
        "extensions": {
            "isf": {
                "skill_id": result.skill_id,
                "skill_version": result.skill_version,
                "confidence_disposition": result.confidence_disposition.value,
                "expanded_capabilities": sorted(c.value for c in result.expanded_capabilities),
                "missing_evidence": [e.value for e in result.missing_evidence],
                "metadata": {
                    k: v
                    for k, v in (result.metadata or {}).items()
                    if k
                    not in {
                        "prompt",
                        "messages",
                        "api_key",
                        "provider_response",
                        "raw_content",
                    }
                },
            }
        },
    }


class ComputerIsfAdapter:
    """Wire adapter: Computer request → SkillEngine → proposal."""

    def __init__(self, engine: SkillEngine | None = None) -> None:
        self.engine = engine or SkillEngine()

    def execute(self, payload: dict[str, Any], *, correlation_id: str = "") -> dict[str, Any]:
        if not isf_enabled():
            raise IsfError(
                IsfErrorCode.ISF_DISABLED,
                "ISF_ENABLED=false; use legacy Computer → Core → AIR path",
            )
        request = skill_request_from_computer(payload, correlation_id=correlation_id)
        # Version check against registry before execute (also done in engine).
        try:
            manifest = self.engine.registry.get(request.skill_id)
        except IsfError:
            raise
        assert_version_compatible(request.skill_version, manifest.version)
        result = self.engine.execute(request)
        return proposal_from_skill_result(result)


# Convenience re-export for evidence type in adapter tests
__all__ = [
    "ComputerIsfAdapter",
    "map_evidence_refs",
    "proposal_from_skill_result",
    "skill_request_from_computer",
    "EvidenceType",
]
