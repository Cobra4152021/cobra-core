"""Authorization audit channel — no credentials stored."""

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
        "credential",
        "session_token",
    }
)


def _scrub(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            k: ("[redacted]" if str(k).lower() in _REDACT else _scrub(v))
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [_scrub(v) for v in value[:100]]
    if isinstance(value, str) and len(value) > 400:
        return value[:400] + "…"
    return value


class SecurityAudit:
    def __init__(self, *, maxlen: int = 2000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def record(
        self,
        event: str,
        *,
        principal_id: str = "",
        resource: str = "",
        action: str = "",
        policy: str = "",
        result: str = "",
        organization_id: str = "",
        department_id: str = "",
        membership: list[str] | tuple[str, ...] | None = None,
        policy_version: str = "",
        authorization_reference: str = "",
        **payload: Any,
    ) -> str:
        entry_id = f"ispf_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "event": event,
            "principal": principal_id,
            "resource": resource,
            "action": action,
            "policy": policy,
            "result": result,
            "organization_id": organization_id,
            "department_id": department_id,
            "membership": list(membership or []),
            "policy_version": policy_version,
            "authorization_reference": authorization_reference,
            "ts": time.time(),
            "channel": "identity_security_policy",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


SECURITY_AUDIT = SecurityAudit()
