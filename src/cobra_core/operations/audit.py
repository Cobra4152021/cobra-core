"""Isolated operations audit — flag/maintenance/quota/admin actions only."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_REDACT = frozenset(
    {
        "authorization",
        "api_key",
        "token",
        "secret",
        "password",
        "x-hidden-grid-key",
        "evidence",
        "case_data",
        "prompt",
    }
)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in _REDACT:
                out[k] = "[redacted]"
            else:
                out[k] = _scrub(v)
        return out
    if isinstance(value, list):
        return [_scrub(v) for v in value[:100]]
    if isinstance(value, str) and len(value) > 400:
        return value[:400] + "…"
    return value


class OperationsAudit:
    def __init__(self, *, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def record(self, event: str, *, actor: str = "system", **payload: Any) -> str:
        entry_id = f"ocp_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "event": event,
            "actor": actor,
            "ts": time.time(),
            "channel": "operations_control_plane",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


OPERATIONS_AUDIT = OperationsAudit()
