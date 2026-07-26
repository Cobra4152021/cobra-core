"""Isolated benchmark audit — never touches production investigation history."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_REDACT_KEYS = frozenset(
    {
        "authorization",
        "api_key",
        "token",
        "secret",
        "password",
        "x-hidden-grid-key",
        "evidence_text",
        "prompt",
    }
)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for k, v in value.items():
            if str(k).lower() in _REDACT_KEYS:
                out[k] = "[redacted]"
            else:
                out[k] = _scrub(v)
        return out
    if isinstance(value, list):
        return [_scrub(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 500:
        return value[:500] + "…"
    return value


class BenchmarkAudit:
    def __init__(self, *, maxlen: int = 500) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def record(self, event: str, **payload: Any) -> str:
        entry_id = f"bm_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "event": event,
            "ts": time.time(),
            "channel": "benchmark_isolated",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


BENCHMARK_AUDIT = BenchmarkAudit()
