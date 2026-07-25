"""ISF audit trail (never records prompts or secrets)."""

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
    ) -> dict[str, Any]:
        entry = {
            "skill": result.skill_id,
            "skill_version": skill_version or result.skill_version,
            "status": result.status.value,
            "expanded_capabilities": sorted(c.value for c in result.expanded_capabilities),
            "confidence_score": result.confidence,
            "confidence_disposition": result.confidence_disposition.value,
            "missing_evidence": [e.value for e in result.missing_evidence],
            "needs_human_review": result.needs_human_review,
            "selected_provider": result.selected_provider,
            "selected_model": result.selected_model,
            "route_reason": result.route_reason,
            "correlation_id": result.correlation_id or None,
            "audit_timestamp_ms": int(time.time() * 1000),
        }
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
