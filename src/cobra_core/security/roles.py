"""Role model — built-in + custom; permissions additive; no admin bypass."""

from __future__ import annotations

import threading
from typing import Any

from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.schemas import BuiltInRole, Permission

# Explicit role → permission sets. Administrator lists every permission — no bypass flag.
_BUILTIN_ROLE_PERMISSIONS: dict[str, frozenset[str]] = {
    BuiltInRole.ADMINISTRATOR.value: frozenset(p.value for p in Permission),
    BuiltInRole.SUPERVISOR.value: frozenset(
        {
            Permission.CREATE_CASE.value,
            Permission.CLOSE_CASE.value,
            Permission.RUN_WORKFLOW.value,
            Permission.APPROVE_WORKFLOW.value,
            Permission.APPROVE_FINDINGS.value,
            Permission.RETRIEVE_EVIDENCE.value,
            Permission.MANAGE_PLUGINS.value,
            Permission.RUN_BENCHMARK.value,
            Permission.VIEW_METRICS.value,
            Permission.MANAGE_OPERATIONS.value,
            Permission.VIEW_AUDIT.value,
            Permission.VIEW_SECURITY.value,
        }
    ),
    BuiltInRole.INVESTIGATOR.value: frozenset(
        {
            Permission.CREATE_CASE.value,
            Permission.RUN_WORKFLOW.value,
            Permission.RETRIEVE_EVIDENCE.value,
            Permission.RUN_BENCHMARK.value,
            Permission.VIEW_METRICS.value,
            Permission.VIEW_SECURITY.value,
        }
    ),
    BuiltInRole.REVIEWER.value: frozenset(
        {
            Permission.APPROVE_WORKFLOW.value,
            Permission.APPROVE_FINDINGS.value,
            Permission.RETRIEVE_EVIDENCE.value,
            Permission.VIEW_METRICS.value,
            Permission.VIEW_SECURITY.value,
        }
    ),
    BuiltInRole.OBSERVER.value: frozenset(
        {
            Permission.VIEW_METRICS.value,
            Permission.VIEW_SECURITY.value,
            # Explicitly no retrieve_evidence — deny via missing permission + policy
        }
    ),
    BuiltInRole.SERVICE.value: frozenset(
        {
            Permission.VIEW_METRICS.value,
            Permission.VIEW_SECURITY.value,
        }
    ),
    BuiltInRole.PLUGIN.value: frozenset(
        {
            Permission.REGISTER_PLUGIN.value,
            Permission.VIEW_SECURITY.value,
        }
    ),
}


class RoleRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._custom: dict[str, set[str]] = {}
        self._assignments: dict[str, set[str]] = {}  # principal_id → roles

    def reset_for_tests(self) -> None:
        with self._lock:
            self._custom.clear()
            self._assignments.clear()

    def list_roles(self) -> list[dict[str, Any]]:
        with self._lock:
            out: list[dict[str, Any]] = []
            for role, builtin_perms in sorted(_BUILTIN_ROLE_PERMISSIONS.items()):
                out.append(
                    {
                        "role": role,
                        "builtin": True,
                        "permissions": sorted(builtin_perms),
                    }
                )
            for role, custom_perms in sorted(self._custom.items()):
                out.append(
                    {
                        "role": role,
                        "builtin": False,
                        "permissions": sorted(custom_perms),
                    }
                )
            return out

    def register_custom(self, role: str, permissions: list[str]) -> None:
        name = (role or "").strip().lower()
        if not name or name in _BUILTIN_ROLE_PERMISSIONS:
            raise SecurityError(SecurityErrorCode.ROLE_NOT_FOUND, "invalid custom role")
        with self._lock:
            self._custom[name] = {p.strip() for p in permissions if p.strip()}

    def permissions_for_roles(self, roles: list[str] | set[str]) -> set[str]:
        """Additive union of permissions across roles. No implicit admin bypass."""
        granted: set[str] = set()
        with self._lock:
            for role in roles:
                key = (role or "").strip().lower()
                if key in _BUILTIN_ROLE_PERMISSIONS:
                    granted |= set(_BUILTIN_ROLE_PERMISSIONS[key])
                elif key in self._custom:
                    granted |= set(self._custom[key])
                else:
                    raise SecurityError(SecurityErrorCode.ROLE_NOT_FOUND, f"unknown role: {role}")
        return granted

    def assign(self, principal_id: str, roles: list[str]) -> list[str]:
        pid = (principal_id or "").strip()
        if not pid:
            raise SecurityError(SecurityErrorCode.PRINCIPAL_NOT_FOUND, "empty principal_id")
        # Validate roles exist
        self.permissions_for_roles(roles)
        with self._lock:
            self._assignments[pid] = {r.strip().lower() for r in roles if r.strip()}
            return sorted(self._assignments[pid])

    def roles_for(self, principal_id: str) -> list[str]:
        with self._lock:
            return sorted(self._assignments.get(principal_id, set()))

    def assignment_count(self) -> int:
        with self._lock:
            return sum(len(v) for v in self._assignments.values())


ROLE_REGISTRY = RoleRegistry()
