"""Public API audit channel."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_REDACT = frozenset({"authorization", "api_key", "token", "secret", "password", "credential"})


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("[redacted]" if str(k).lower() in _REDACT else _scrub(v)) for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value[:50]]
    if isinstance(value, str) and len(value) > 400:
        return value[:400] + "…"
    return value


class ApiAudit:
    def __init__(self, *, maxlen: int = 2000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def record(
        self,
        *,
        api_client: str,
        organization_id: str,
        endpoint: str,
        result: str,
        latency_ms: float,
        authorization: str = "",
        request_id: str = "",
        **payload: Any,
    ) -> str:
        entry_id = f"pasf_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "api_client": api_client,
            "organization_id": organization_id,
            "endpoint": endpoint,
            "result": result,
            "latency_ms": round(latency_ms, 2),
            "authorization": authorization,  # decision ref only, never bearer token
            "request_id": request_id,
            "ts": time.time(),
            "channel": "public_api_sdk",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


API_AUDIT = ApiAudit()
