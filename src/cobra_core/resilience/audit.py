"""RRF audit trail (never prompts/secrets/evidence bodies)."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any


class ResilienceAuditLog:
    def __init__(self, *, maxlen: int = 2000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def record(self, entry: dict[str, Any]) -> dict[str, Any]:
        safe = {
            k: v
            for k, v in entry.items()
            if k
            not in {
                "prompt",
                "messages",
                "api_key",
                "provider_response",
                "raw_content",
                "evidence_text",
            }
        }
        safe.setdefault("timestamp", int(time.time() * 1000))
        with self._lock:
            self._entries.append(safe)
        return safe

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._entries)
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


RRF_AUDIT = ResilienceAuditLog()
