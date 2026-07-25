"""ISF audit trail (never records prompts, secrets, or raw evidence)."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

from cobra_core.isf.types import SkillResult


class IsfAuditLog:
    """Bounded in-memory audit of skill executions (safe fields only)."""

    def __init__(self, *, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def record(
        self,
        result: SkillResult,
        *,
        skill_version: str | None = None,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        meta = result.metadata or {}
        entry: dict[str, Any] = {
            "correlation_id": result.correlation_id or None,
            "skill_id": result.skill_id,
            "skill": result.skill_id,  # KC-024 compat
            "skill_version": skill_version or result.skill_version,
            "manifest_version": meta.get("manifest_version") or result.skill_version,
            "requested_profile": meta.get("requested_profile"),
            "required_capabilities": meta.get("required_capabilities")
            or sorted(c.value for c in result.expanded_capabilities),
            "optional_capabilities_used": meta.get("optional_capabilities_used") or [],
            "required_evidence_types": meta.get("required_evidence_types") or [],
            "evidence_validation_result": meta.get("evidence_validation_result")
            or ("fail" if result.missing_evidence else "pass"),
            "selected_provider": result.selected_provider,
            "selected_model": result.selected_model,
            "routing_reason": result.route_reason or meta.get("routing_reason"),
            "route_reason": result.route_reason,  # KC-024 compat
            "schema_name": meta.get("schema_name"),
            "schema_validation_result": meta.get("schema_validation_result"),
            "repair_attempt_count": int(meta.get("repair_attempt_count") or 0),
            "confidence": result.confidence,
            "confidence_score": result.confidence,  # KC-024 compat
            "confidence_threshold": meta.get("confidence_threshold"),
            "confidence_disposition": result.confidence_disposition.value,
            "needs_human_review": result.needs_human_review,
            "execution_status": result.status.value,
            "status": result.status.value,  # KC-024 compat
            "expanded_capabilities": sorted(c.value for c in result.expanded_capabilities),
            "missing_evidence": [e.value for e in result.missing_evidence],
            "timestamp": int(time.time() * 1000),
            "audit_timestamp_ms": int(time.time() * 1000),
        }
        if extra:
            for k, v in extra.items():
                if k in {
                    "prompt",
                    "messages",
                    "api_key",
                    "provider_response",
                    "raw_content",
                    "evidence_text",
                }:
                    continue
                entry[k] = v
        with self._lock:
            self._entries.append(entry)
        return entry

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._entries)
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


ISF_AUDIT = IsfAuditLog()
