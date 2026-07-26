"""Identity helpers — users, services, system principal bootstrap."""

from __future__ import annotations

from typing import Any

from cobra_core.security.principals import PRINCIPAL_REGISTRY, Principal, PrincipalRegistry
from cobra_core.security.roles import ROLE_REGISTRY, RoleRegistry
from cobra_core.security.schemas import BuiltInRole, PrincipalType

# Least-privilege service identities (KC-034).
SERVICE_IDENTITIES: dict[str, dict[str, Any]] = {
    "svc_evidence_vault": {
        "display_name": "Evidence Vault Service",
        "roles": [BuiltInRole.SERVICE.value],
        "extra_permissions": ["retrieve_evidence"],
    },
    "svc_operations": {
        "display_name": "Operations Service",
        "roles": [BuiltInRole.SERVICE.value],
        "extra_permissions": ["manage_operations", "view_metrics"],
    },
    "svc_benchmark": {
        "display_name": "Benchmark Service",
        "roles": [BuiltInRole.SERVICE.value],
        "extra_permissions": ["run_benchmark", "view_metrics"],
    },
}


class IdentityService:
    """Resolves and bootstraps principals. Does not change routing/AI behavior."""

    def __init__(
        self,
        *,
        principals: PrincipalRegistry | None = None,
        roles: RoleRegistry | None = None,
    ) -> None:
        self.principals = principals if principals is not None else PRINCIPAL_REGISTRY
        self.roles = roles if roles is not None else ROLE_REGISTRY
        self._extra_permissions: dict[str, set[str]] = {}
        self._bootstrapped = False

    def reset_for_tests(self) -> None:
        self.principals.reset_for_tests()
        self._extra_permissions.clear()
        self._bootstrapped = False

    def bootstrap(self) -> list[str]:
        """Create system + least-privilege service principals."""
        if self._bootstrapped:
            return [p["principal_id"] for p in self.principals.list_public()]
        system = self.principals.create(
            principal_type=PrincipalType.SYSTEM,
            display_name="Cobra System",
            roles=[BuiltInRole.ADMINISTRATOR.value],
            principal_id="sys_cobra",
        )
        self.roles.assign(system.principal_id, system.roles)
        created = [system.principal_id]
        for sid, meta in SERVICE_IDENTITIES.items():
            p = self.principals.create(
                principal_type=PrincipalType.SERVICE,
                display_name=str(meta["display_name"]),
                roles=list(meta["roles"]),
                principal_id=sid,
            )
            self.roles.assign(p.principal_id, p.roles)
            extras = {str(x) for x in meta.get("extra_permissions") or []}
            self._extra_permissions[sid] = extras
            created.append(sid)
        self._bootstrapped = True
        return created

    def ensure_bootstrapped(self) -> None:
        if not self._bootstrapped:
            self.bootstrap()

    def create_user(
        self,
        *,
        display_name: str,
        roles: list[str],
        principal_id: str | None = None,
    ) -> Principal:
        self.ensure_bootstrapped()
        p = self.principals.create(
            principal_type=PrincipalType.USER,
            display_name=display_name,
            roles=roles,
            principal_id=principal_id,
        )
        self.roles.assign(p.principal_id, roles)
        return p

    def create_api_client(
        self,
        *,
        display_name: str,
        roles: list[str],
        principal_id: str | None = None,
    ) -> Principal:
        self.ensure_bootstrapped()
        p = self.principals.create(
            principal_type=PrincipalType.API_CLIENT,
            display_name=display_name,
            roles=roles,
            principal_id=principal_id,
        )
        self.roles.assign(p.principal_id, roles)
        return p

    def resolve(self, principal_id: str) -> Principal:
        self.ensure_bootstrapped()
        return self.principals.get(principal_id)

    def effective_permissions(self, principal_id: str) -> set[str]:
        self.ensure_bootstrapped()
        p = self.principals.get(principal_id)
        roles = self.roles.roles_for(principal_id) or list(p.roles)
        granted = self.roles.permissions_for_roles(roles)
        granted |= self._extra_permissions.get(principal_id, set())
        return granted


IDENTITY = IdentityService()
