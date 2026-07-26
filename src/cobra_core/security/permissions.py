"""Permission registry — additive, explicit, no implicit grants."""

from __future__ import annotations

from typing import Any

from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.schemas import Permission


class PermissionRegistry:
    """Canonical permission names for ISPF."""

    def __init__(self) -> None:
        self._builtin = {p.value for p in Permission}
        self._custom: set[str] = set()

    def register_custom(self, name: str) -> str:
        key = (name or "").strip()
        if not key or "/" in key or "\\" in key or " " in key:
            raise SecurityError(SecurityErrorCode.PERMISSION_UNKNOWN, "invalid permission name")
        if key not in self._builtin:
            self._custom.add(key)
        return key

    def known(self) -> list[str]:
        return sorted(self._builtin | self._custom)

    def is_known(self, name: str) -> bool:
        key = (name or "").strip()
        return key in self._builtin or key in self._custom

    def resolve(self, name: str) -> str:
        key = (name or "").strip()
        if not self.is_known(key):
            raise SecurityError(SecurityErrorCode.PERMISSION_UNKNOWN, f"unknown permission: {key}")
        return key

    def public_list(self) -> list[dict[str, Any]]:
        return [{"permission": p, "builtin": p in self._builtin} for p in self.known()]

    def reset_for_tests(self) -> None:
        self._custom.clear()


PERMISSION_REGISTRY = PermissionRegistry()
