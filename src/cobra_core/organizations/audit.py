"""Organization-scoped audit channel."""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from typing import Any

_REDACT = frozenset(
    {"authorization", "api_key", "token", "secret", "password", "credential", "session_token"}
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


class OrganizationAudit:
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
        organization_id: str,
        department_id: str = "",
        principal_id: str = "",
        membership: list[str] | None = None,
        policy_version: str = "motf-1",
        authorization_reference: str = "",
        **payload: Any,
    ) -> str:
        entry_id = f"motf_{uuid.uuid4().hex[:12]}"
        item = {
            "id": entry_id,
            "event": event,
            "organization_id": organization_id,
            "department_id": department_id,
            "principal_id": principal_id,
            "membership": list(membership or []),
            "policy_version": policy_version,
            "authorization_reference": authorization_reference,
            "ts": time.time(),
            "channel": "multi_organization_tenancy",
            "payload": _scrub(payload),
        }
        with self._lock:
            self._entries.appendleft(item)
        return entry_id

    def for_organization(self, organization_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        oid = organization_id.strip()
        with self._lock:
            return [e for e in self._entries if e.get("organization_id") == oid][
                : max(1, min(limit, 200))
            ]

    def recent(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._entries)[: max(1, min(limit, 200))]


ORGANIZATION_AUDIT = OrganizationAudit()
