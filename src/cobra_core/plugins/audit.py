"""Isolated plugin audit channel."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_REDACT = frozenset({"authorization", "api_key", "token", "secret", "signature", "checksum"})


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("[redacted]" if str(k).lower() in _REDACT else _scrub(v)) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value[:100]]
    if isinstance(value, str) and len(value) > 400:
        return value[:400] + "…"
    return value


class PluginAudit:
    def __init__(self, *, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def record(self, event: str, *, actor: str = "system", **payload: Any) -> str:
        entry_id = f"pef_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "event": event,
            "actor": actor,
            "ts": time.time(),
            "channel": "plugin_extension_framework",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


PLUGIN_AUDIT = PluginAudit()
