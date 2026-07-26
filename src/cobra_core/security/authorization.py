"""
Central authorization engine.

Every protected subsystem should call authorize() — no routing/AI/workflow changes here.
Deterministic: deny policies win, then allow/conditional, else default deny.
No implicit administrator bypass.
KC-035: tenant-aware when organization_id is supplied.
"""

from __future__ import annotations

from typing import Any

from cobra_core.security.audit import SECURITY_AUDIT
from cobra_core.security.config import SecurityConfig, load_security_config
from cobra_core.security.errors import SecurityError, SecurityErrorCode
from cobra_core.security.identity import IDENTITY, IdentityService
from cobra_core.security.metrics import SECURITY_METRICS
from cobra_core.security.policy import POLICY_ENGINE, PolicyEngine
from cobra_core.security.roles import ROLE_REGISTRY, RoleRegistry
from cobra_core.security.schemas import (
    ACTION_PERMISSIONS,
    AuthzDecision,
    DecisionEffect,
    PrincipalType,
    ResourceRef,
    ResourceType,
)


class AuthorizationEngine:
    def __init__(
        self,
        *,
        config: SecurityConfig | None = None,
        identity: IdentityService | None = None,
        policies: PolicyEngine | None = None,
        roles: RoleRegistry | None = None,
    ) -> None:
        self.config = config or load_security_config()
        self.identity = identity if identity is not None else IDENTITY
        self.policies = policies if policies is not None else POLICY_ENGINE
        self.roles = roles if roles is not None else ROLE_REGISTRY

    def reset_for_tests(self) -> None:
        self.config = load_security_config()

    def authorize(
        self,
        *,
        principal_id: str,
        action: str,
        resource: ResourceRef | None = None,
        resource_type: ResourceType | str | None = None,
        resource_id: str = "*",
        attributes: dict[str, Any] | None = None,
        organization_id: str = "",
        department_id: str = "",
    ) -> AuthzDecision:
        tenant_org = (organization_id or "").strip()
        tenant_dept = (department_id or "").strip()
        membership_roles: tuple[str, ...] = ()
        policy_version = ""

        if not self.config.enabled:
            audit_ref = SECURITY_AUDIT.record(
                "authorization",
                principal_id=principal_id,
                action=action,
                result="deny",
                policy="ispf_disabled",
                resource=str(resource_type or ""),
                organization_id=tenant_org,
                department_id=tenant_dept,
            )
            SECURITY_METRICS.record_authz(allowed=False, policy_evals=0)
            return AuthzDecision(
                effect=DecisionEffect.DENY,
                reason="ISPF disabled",
                policy_id="ispf_disabled",
                audit_ref=audit_ref,
                principal_id=principal_id,
                action=action,
                resource_type=str(resource_type or ""),
                organization_id=tenant_org,
                department_id=tenant_dept,
            )

        self.identity.ensure_bootstrapped()
        principal = self.identity.resolve(principal_id)
        if not principal.active:
            return self._decide(
                effect=DecisionEffect.DENY,
                reason="principal inactive",
                policy_id="principal_inactive",
                principal_id=principal_id,
                action=action,
                resource_type="",
                policy_evals=0,
                organization_id=tenant_org,
                department_id=tenant_dept,
            )

        if resource is None:
            if resource_type is None:
                raise SecurityError(SecurityErrorCode.POLICY_INVALID, "resource_type required")
            rtype = (
                resource_type
                if isinstance(resource_type, ResourceType)
                else ResourceType(str(resource_type))
            )
            resource = ResourceRef(
                resource_type=rtype,
                resource_id=resource_id,
                attributes=dict(attributes or {}),
            )

        # --- KC-035 tenancy gate ---
        resource_org = str(resource.attributes.get("organization_id") or "").strip()
        if resource_org and not tenant_org:
            return self._decide(
                effect=DecisionEffect.DENY,
                reason="tenant context required for organization-scoped resource",
                policy_id="tenant_context_required",
                principal_id=principal_id,
                action=action,
                resource_type=resource.resource_type.value,
                policy_evals=1,
            )
        if tenant_org:
            try:
                from cobra_core.organizations.tenancy import TENANCY
                from cobra_core.organizations.validation import OrganizationValidationError

                try:
                    ctx = TENANCY.resolve_context(
                        principal_id=principal_id,
                        organization_id=tenant_org,
                        department_id=tenant_dept,
                    )
                except OrganizationValidationError as exc:
                    # System principal may operate without membership for bootstrap only
                    # when explicitly typed system and org exists — still no cross-org resource.
                    if principal.principal_type != PrincipalType.SYSTEM:
                        return self._decide(
                            effect=DecisionEffect.DENY,
                            reason=exc.message,
                            policy_id="cross_org_denied",
                            principal_id=principal_id,
                            action=action,
                            resource_type=resource.resource_type.value,
                            policy_evals=1,
                            organization_id=tenant_org,
                            department_id=tenant_dept,
                        )
                    ctx = None
                    policy_version = TENANCY.config.policy_version
                if ctx is not None:
                    membership_roles = ctx.membership_roles
                    policy_version = ctx.policy_version
                    tenant_dept = ctx.department_id
            except ImportError as exc:
                return self._decide(
                    effect=DecisionEffect.DENY,
                    reason=f"tenancy enforcement unavailable: {type(exc).__name__}",
                    policy_id="tenancy_unavailable",
                    principal_id=principal_id,
                    action=action,
                    resource_type=resource.resource_type.value,
                    policy_evals=1,
                    organization_id=tenant_org,
                    department_id=tenant_dept,
                )

            res_org = resource_org
            if res_org and res_org != tenant_org:
                return self._decide(
                    effect=DecisionEffect.DENY,
                    reason="cross-organization access denied",
                    policy_id="cross_org_denied",
                    principal_id=principal_id,
                    action=action,
                    resource_type=resource.resource_type.value,
                    policy_evals=1,
                    organization_id=tenant_org,
                    department_id=tenant_dept,
                    membership=membership_roles,
                    policy_version=policy_version,
                )

        # Roles/permissions: org membership roles when tenant context present.
        if membership_roles:
            roles: set[str] = set()
            for mr in membership_roles:
                from cobra_core.organizations.schemas import (
                    MEMBERSHIP_TO_ISPF_ROLES,
                    MembershipRole,
                )

                try:
                    mapped = MEMBERSHIP_TO_ISPF_ROLES.get(MembershipRole(mr), ())
                except ValueError:
                    mapped = ()
                roles.update(mapped)
            permissions = self.roles.permissions_for_roles(roles) if roles else set()
        else:
            roles = set(self.roles.roles_for(principal_id) or principal.roles)
            permissions = self.identity.effective_permissions(principal_id)

        SECURITY_METRICS.set_role_assignments(self.roles.assignment_count())

        required = ACTION_PERMISSIONS.get(action)
        required_name = required.value if required else None

        matches = self.policies.matching_rules(
            principal_id=principal_id,
            roles=roles,
            action=action,
            resource=resource,
        )
        evals = len(matches) + 1

        # 1) Explicit deny wins
        for rule in matches:
            if rule.effect == DecisionEffect.DENY:
                return self._decide(
                    effect=DecisionEffect.DENY,
                    reason=rule.description or "denied by policy",
                    policy_id=rule.policy_id,
                    principal_id=principal_id,
                    action=action,
                    resource_type=resource.resource_type.value,
                    required_permission=required_name,
                    policy_evals=evals,
                    organization_id=tenant_org,
                    department_id=tenant_dept,
                    membership=membership_roles,
                    policy_version=policy_version,
                )

        # 2) Conditional owner match
        for rule in matches:
            if rule.effect != DecisionEffect.CONDITIONAL:
                continue
            owner = resource.attributes.get("owner")
            if owner is None:
                continue
            if owner == principal_id:
                if required_name and required_name not in permissions:
                    return self._decide(
                        effect=DecisionEffect.DENY,
                        reason=f"missing permission {required_name}",
                        policy_id="permission_required",
                        principal_id=principal_id,
                        action=action,
                        resource_type=resource.resource_type.value,
                        required_permission=required_name,
                        policy_evals=evals,
                        organization_id=tenant_org,
                        department_id=tenant_dept,
                        membership=membership_roles,
                        policy_version=policy_version,
                    )
                return self._decide(
                    effect=DecisionEffect.ALLOW,
                    reason="conditional owner match",
                    policy_id=rule.policy_id,
                    principal_id=principal_id,
                    action=action,
                    resource_type=resource.resource_type.value,
                    required_permission=required_name,
                    conditions={"owner": owner},
                    policy_evals=evals,
                    organization_id=tenant_org,
                    department_id=tenant_dept,
                    membership=membership_roles,
                    policy_version=policy_version,
                )
            return self._decide(
                effect=DecisionEffect.CONDITIONAL,
                reason="conditional owner mismatch",
                policy_id=rule.policy_id,
                principal_id=principal_id,
                action=action,
                resource_type=resource.resource_type.value,
                required_permission=required_name,
                conditions={"required": "owner==principal", "owner": owner},
                policy_evals=evals,
                organization_id=tenant_org,
                department_id=tenant_dept,
                membership=membership_roles,
                policy_version=policy_version,
            )

        # 3) Explicit allow policies
        for rule in matches:
            if rule.effect == DecisionEffect.ALLOW:
                if required_name and required_name not in permissions:
                    return self._decide(
                        effect=DecisionEffect.DENY,
                        reason=f"missing permission {required_name}",
                        policy_id="permission_required",
                        principal_id=principal_id,
                        action=action,
                        resource_type=resource.resource_type.value,
                        required_permission=required_name,
                        policy_evals=evals,
                        organization_id=tenant_org,
                        department_id=tenant_dept,
                        membership=membership_roles,
                        policy_version=policy_version,
                    )
                return self._decide(
                    effect=DecisionEffect.ALLOW,
                    reason=rule.description or "allowed by policy",
                    policy_id=rule.policy_id,
                    principal_id=principal_id,
                    action=action,
                    resource_type=resource.resource_type.value,
                    required_permission=required_name,
                    policy_evals=evals,
                    organization_id=tenant_org,
                    department_id=tenant_dept,
                    membership=membership_roles,
                    policy_version=policy_version,
                )

        # 4) Permission-grant allow
        if required_name and required_name in permissions:
            return self._decide(
                effect=DecisionEffect.ALLOW,
                reason="allowed by role permission grant",
                policy_id="pol_permission_grant_allow",
                principal_id=principal_id,
                action=action,
                resource_type=resource.resource_type.value,
                required_permission=required_name,
                policy_evals=evals,
                organization_id=tenant_org,
                department_id=tenant_dept,
                membership=membership_roles,
                policy_version=policy_version,
            )

        # 5) Default deny
        return self._decide(
            effect=DecisionEffect.DENY,
            reason="default deny",
            policy_id="default_deny",
            principal_id=principal_id,
            action=action,
            resource_type=resource.resource_type.value,
            required_permission=required_name,
            policy_evals=evals,
            organization_id=tenant_org,
            department_id=tenant_dept,
            membership=membership_roles,
            policy_version=policy_version,
        )

    def require(
        self,
        *,
        principal_id: str,
        action: str,
        resource: ResourceRef | None = None,
        **kwargs: Any,
    ) -> AuthzDecision:
        decision = self.authorize(
            principal_id=principal_id,
            action=action,
            resource=resource,
            **kwargs,
        )
        if decision.effect != DecisionEffect.ALLOW:
            raise SecurityError(
                SecurityErrorCode.AUTHORIZATION_DENIED,
                f"{decision.effect.value}: {decision.reason}",
            )
        return decision

    def _decide(
        self,
        *,
        effect: DecisionEffect,
        reason: str,
        policy_id: str,
        principal_id: str,
        action: str,
        resource_type: str,
        required_permission: str | None = None,
        conditions: dict[str, Any] | None = None,
        policy_evals: int = 1,
        organization_id: str = "",
        department_id: str = "",
        membership: tuple[str, ...] = (),
        policy_version: str = "",
    ) -> AuthzDecision:
        allowed = effect == DecisionEffect.ALLOW
        audit_ref = SECURITY_AUDIT.record(
            "authorization",
            principal_id=principal_id,
            resource=resource_type,
            action=action,
            policy=policy_id,
            result=effect.value,
            reason=reason,
            required_permission=required_permission,
            organization_id=organization_id,
            department_id=department_id,
            membership=list(membership),
            policy_version=policy_version,
        )
        SECURITY_METRICS.record_authz(allowed=allowed, policy_evals=policy_evals)
        return AuthzDecision(
            effect=effect,
            reason=reason,
            policy_id=policy_id,
            audit_ref=audit_ref,
            principal_id=principal_id,
            action=action,
            resource_type=resource_type,
            required_permission=required_permission,
            conditions=dict(conditions or {}),
            organization_id=organization_id,
            department_id=department_id,
            membership=membership,
            policy_version=policy_version,
        )


AUTHORIZATION = AuthorizationEngine()


def authorize(
    *,
    principal_id: str,
    action: str,
    resource: ResourceRef | None = None,
    resource_type: ResourceType | str | None = None,
    resource_id: str = "*",
    attributes: dict[str, Any] | None = None,
    organization_id: str = "",
    department_id: str = "",
) -> AuthzDecision:
    """Public entrypoint for subsystem authorization checks."""
    return AUTHORIZATION.authorize(
        principal_id=principal_id,
        action=action,
        resource=resource,
        resource_type=resource_type,
        resource_id=resource_id,
        attributes=attributes,
        organization_id=organization_id,
        department_id=department_id,
    )
