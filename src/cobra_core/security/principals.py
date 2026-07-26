"""Authenticated principals — exactly one per request context."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.schemas import PrincipalType


@dataclass
class Principal:
    principal_id: str
    principal_type: PrincipalType
    display_name: str
    roles: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    active: bool = True
    created_at: float = field(default_factory=time.time)

    def public_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "principal_type": self.principal_type.value,
            "display_name": self.display_name,
            "roles": list(self.roles),
            "attributes": {
                k: v
                for k, v in self.attributes.items()
                if str(k).lower() not in {"password", "secret", "token", "api_key", "authorization"}
            },
            "active": self.active,
        }


class PrincipalRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._principals: dict[str, Principal] = {}

    def reset_for_tests(self) -> None:
        with self._lock:
            self._principals.clear()

    def put(self, principal: Principal) -> Principal:
        with self._lock:
            self._principals[principal.principal_id] = principal
            return principal

    def get(self, principal_id: str) -> Principal:
        with self._lock:
            try:
                return self._principals[principal_id]
            except KeyError as exc:
                raise SecurityError(
                    SecurityErrorCode.PRINCIPAL_NOT_FOUND,
                    f"principal not found: {principal_id}",
                ) from exc

    def create(
        self,
        *,
        principal_type: PrincipalType,
        display_name: str,
        roles: list[str] | None = None,
        principal_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> Principal:
        pid = (principal_id or f"{principal_type.value}_{uuid.uuid4().hex[:12]}").strip()
        p = Principal(
            principal_id=pid,
            principal_type=principal_type,
            display_name=display_name.strip() or pid,
            roles=list(roles or []),
            attributes=dict(attributes or {}),
        )
        return self.put(p)

    def list_public(self) -> list[dict[str, Any]]:
        with self._lock:
            return [self._principals[k].public_dict() for k in sorted(self._principals)]


PRINCIPAL_REGISTRY = PrincipalRegistry()
