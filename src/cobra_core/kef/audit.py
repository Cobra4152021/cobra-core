"""KEF audit trail — never stores document bodies, prompts, or secrets."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_FORBIDDEN = frozenset(
    {
        "prompt",
        "messages",
        "api_key",
        "provider_response",
        "raw_content",
        "evidence_text",
        "text",
        "body",
        "content",
        "document_body",
    }
)


class KefAuditLog:
    def __init__(self, *, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def record(self, event: dict[str, Any]) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "audit_id": event.get("audit_id") or str(uuid.uuid4()),
            "correlation_id": event.get("correlation_id"),
            "skill_id": event.get("skill_id"),
            "connector": event.get("connector"),
            "connectors": event.get("connectors") or [],
            "query_type": event.get("query_type"),
            "filters": event.get("filters") or {},
            "returned_count": int(event.get("returned_count") or 0),
            "duplicates_removed": int(event.get("duplicates_removed") or 0),
            "ranking_top_ids": list(event.get("ranking_top_ids") or [])[:20],
            "citations_produced": list(event.get("citations_produced") or [])[:50],
            "permission_failures": int(event.get("permission_failures") or 0),
            "missing_required": list(event.get("missing_required") or []),
            "status": event.get("status") or "ok",
            "latency_ms": int(event.get("latency_ms") or 0),
            "timestamp": int(time.time() * 1000),
        }
        for k, v in event.items():
            if k in entry or k in _FORBIDDEN:
                continue
            if k.endswith("_text") or k.endswith("_body"):
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


KEF_AUDIT = KefAuditLog()
