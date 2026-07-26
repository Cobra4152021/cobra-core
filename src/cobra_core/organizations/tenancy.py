"""Tenant isolation — every resource belongs to exactly one organization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from cobra_core.organizations.config import OrganizationsConfig, load_organizations_config
from cobra_core.organizations.membership import MEMBERSHIP_REGISTRY, MembershipRegistry
from cobra_core.organizations.registry import ORGANIZATION_REGISTRY, OrganizationRegistry
from cobra_core.organizations.schemas import ResourceKind, ResourceOwnership
from cobra_core.organizations.validation import OrganizationValidationError


@dataclass(frozen=True)
class TenantContext:
    organization_id: str
    department_id: str = ""
    principal_id: str = ""
    membership_roles: tuple[str, ...] = ()
    policy_version: str = "motf-1"

    def public_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "department_id": self.department_id,
            "principal_id": self.principal_id,
            "membership_roles": list(self.membership_roles),
            "policy_version": self.policy_version,
        }


class TenancyService:
    def __init__(
        self,
        *,
        registry: OrganizationRegistry | None = None,
        membership: MembershipRegistry | None = None,
        config: OrganizationsConfig | None = None,
    ) -> None:
        self.registry = registry if registry is not None else ORGANIZATION_REGISTRY
        self.membership = membership if membership is not None else MEMBERSHIP_REGISTRY
        self.config = config or load_organizations_config()

    def reset_for_tests(self) -> None:
        self.registry.reset_for_tests()
        self.config = load_organizations_config()

    def resolve_context(
        self,
        *,
        principal_id: str,
        organization_id: str,
        department_id: str = "",
    ) -> TenantContext:
        if not self.config.enabled:
            raise OrganizationValidationError("motf_disabled", "MOTF disabled")
        org = self.registry.get(organization_id)
        if not self.membership.has_membership(principal_id, org.organization_id):
            raise OrganizationValidationError(
                "cross_org_denied",
                "principal is not a member of organization",
            )
        m = self.membership.get(principal_id, org.organization_id)
        if not m.active:
            raise OrganizationValidationError("membership_inactive", "membership inactive")
        if department_id:
            dept = self.registry.get_department(department_id)
            if dept.organization_id != org.organization_id:
                raise OrganizationValidationError(
                    "dept_mismatch", "department not in organization"
                )
            if m.department_ids and department_id not in m.department_ids:
                # Department-scoped memberships must match; empty list = org-wide.
                raise OrganizationValidationError(
                    "dept_denied", "principal not assigned to department"
                )
        return TenantContext(
            organization_id=org.organization_id,
            department_id=department_id or "",
            principal_id=principal_id,
            membership_roles=tuple(r.value for r in m.roles),
            policy_version=str(
                org.security_policies.get("policy_version") or self.config.policy_version
            ),
        )

    def assert_same_organization(
        self,
        *,
        organization_id: str,
        ownership: ResourceOwnership,
    ) -> None:
        if ownership.organization_id != organization_id:
            if self.config.allow_cross_org:
                return
            raise OrganizationValidationError(
                "cross_org_denied",
                f"resource {ownership.resource_id} belongs to {ownership.organization_id}",
            )

    def assert_resource_access(
        self,
        *,
        principal_id: str,
        organization_id: str,
        resource_kind: ResourceKind | str,
        resource_id: str,
        department_id: str = "",
    ) -> ResourceOwnership:
        ctx = self.resolve_context(
            principal_id=principal_id,
            organization_id=organization_id,
            department_id=department_id,
        )
        ownership = self.registry.ownership_of(resource_kind, resource_id)
        self.assert_same_organization(organization_id=ctx.organization_id, ownership=ownership)
        return ownership

    def move_case(
        self,
        *,
        actor_principal_id: str,
        case_id: str,
        from_organization_id: str,
        to_organization_id: str,
        to_department_id: str = "",
    ) -> ResourceOwnership:
        """
        Administrative case move — requires org admin membership + audit (caller records audit).
        Re-tags ownership (exception to immutability for explicit admin move only).
        """
        from_ctx = self.resolve_context(
            principal_id=actor_principal_id,
            organization_id=from_organization_id,
        )
        if not any(
            r in {"organization_owner", "organization_administrator"}
            for r in from_ctx.membership_roles
        ):
            raise OrganizationValidationError(
                "move_unauthorized",
                "case move requires organization owner or administrator",
            )
        # Must also be admin in destination
        to_ctx = self.resolve_context(
            principal_id=actor_principal_id,
            organization_id=to_organization_id,
            department_id=to_department_id,
        )
        if not any(
            r in {"organization_owner", "organization_administrator"}
            for r in to_ctx.membership_roles
        ):
            raise OrganizationValidationError(
                "move_unauthorized",
                "case move requires admin membership in destination organization",
            )
        old = self.registry.ownership_of(ResourceKind.CASE, case_id)
        self.assert_same_organization(organization_id=from_organization_id, ownership=old)
        # Replace ownership entry (admin move path)
        key = f"{ResourceKind.CASE.value}:{case_id}"
        new_ownership = ResourceOwnership(
            organization_id=to_organization_id,
            department_id=to_department_id or "",
            resource_owner=old.resource_owner,
            classification=old.classification,
            creation_time=old.creation_time,
            resource_kind=ResourceKind.CASE,
            resource_id=case_id,
        )
        with self.registry._lock:  # noqa: SLF001 — controlled admin path
            self.registry._ownership[key] = new_ownership
        return new_ownership


TENANCY = TenancyService()
