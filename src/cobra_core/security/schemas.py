"""ISPF identity, role, permission, resource, and decision schemas."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PrincipalType(StrEnum):
    USER = "user"
    SERVICE = "service"
    API_CLIENT = "api_client"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    SYSTEM = "system"


class BuiltInRole(StrEnum):
    ADMINISTRATOR = "administrator"
    SUPERVISOR = "supervisor"
    INVESTIGATOR = "investigator"
    REVIEWER = "reviewer"
    OBSERVER = "observer"
    SERVICE = "service"
    PLUGIN = "plugin"


class Permission(StrEnum):
    CREATE_CASE = "create_case"
    CLOSE_CASE = "close_case"
    RUN_WORKFLOW = "run_workflow"
    APPROVE_WORKFLOW = "approve_workflow"
    APPROVE_FINDINGS = "approve_findings"
    RETRIEVE_EVIDENCE = "retrieve_evidence"
    REGISTER_PLUGIN = "register_plugin"
    MANAGE_PLUGINS = "manage_plugins"
    RUN_BENCHMARK = "run_benchmark"
    VIEW_METRICS = "view_metrics"
    MANAGE_OPERATIONS = "manage_operations"
    MANAGE_USERS = "manage_users"
    VIEW_AUDIT = "view_audit"
    MANAGE_ROLES = "manage_roles"
    MANAGE_POLICIES = "manage_policies"
    VIEW_SECURITY = "view_security"


class ResourceType(StrEnum):
    CASE = "case"
    WORKFLOW = "workflow"
    EVIDENCE = "evidence"
    FINDING = "finding"
    PLUGIN = "plugin"
    DATASET = "dataset"
    REPORT = "report"
    BENCHMARK = "benchmark"
    OPERATIONS = "operations"
    SYSTEM = "system"


class DecisionEffect(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    CONDITIONAL = "conditional"


class AuthMethod(StrEnum):
    BEARER = "bearer"
    SERVICE = "service"
    SYSTEM = "system"
    SESSION = "session"
    INTERNAL = "internal"


# Action string → required permission (deterministic mapping).
ACTION_PERMISSIONS: dict[str, Permission] = {
    "create_case": Permission.CREATE_CASE,
    "close_case": Permission.CLOSE_CASE,
    "run_workflow": Permission.RUN_WORKFLOW,
    "approve_workflow": Permission.APPROVE_WORKFLOW,
    "approve_findings": Permission.APPROVE_FINDINGS,
    "retrieve_evidence": Permission.RETRIEVE_EVIDENCE,
    "register_plugin": Permission.REGISTER_PLUGIN,
    "manage_plugins": Permission.MANAGE_PLUGINS,
    "run_benchmark": Permission.RUN_BENCHMARK,
    "view_metrics": Permission.VIEW_METRICS,
    "manage_operations": Permission.MANAGE_OPERATIONS,
    "manage_users": Permission.MANAGE_USERS,
    "view_audit": Permission.VIEW_AUDIT,
    "manage_roles": Permission.MANAGE_ROLES,
    "manage_policies": Permission.MANAGE_POLICIES,
    "view_security": Permission.VIEW_SECURITY,
}


@dataclass(frozen=True)
class ResourceRef:
    resource_type: ResourceType
    resource_id: str = "*"
    attributes: dict[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "resource_type": self.resource_type.value,
            "resource_id": self.resource_id,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class AuthzDecision:
    effect: DecisionEffect
    reason: str
    policy_id: str
    audit_ref: str
    principal_id: str
    action: str
    resource_type: str
    required_permission: str | None = None
    conditions: dict[str, Any] = field(default_factory=dict)
    # KC-035 tenant-aware fields (empty when not in org context)
    organization_id: str = ""
    department_id: str = ""
    membership: tuple[str, ...] = ()
    policy_version: str = ""

    def allowed(self) -> bool:
        return self.effect == DecisionEffect.ALLOW

    def public_dict(self) -> dict[str, Any]:
        return {
            "effect": self.effect.value,
            "reason": self.reason,
            "policy_id": self.policy_id,
            "audit_ref": self.audit_ref,
            "principal_id": self.principal_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "required_permission": self.required_permission,
            "conditions": dict(self.conditions),
            "organization_id": self.organization_id,
            "department_id": self.department_id,
            "membership": list(self.membership),
            "policy_version": self.policy_version,
        }
