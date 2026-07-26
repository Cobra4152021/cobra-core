"""MOTF schemas — organizations, departments, membership, ownership, scope."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class OrganizationStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class Classification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class DepartmentKind(StrEnum):
    SHERIFF = "sheriff"
    POLICE = "police"
    COMPLIANCE = "compliance"
    INTERNAL_AFFAIRS = "internal_affairs"
    UNION = "union"
    INSPECTOR_GENERAL = "inspector_general"
    RISK_MANAGEMENT = "risk_management"
    CUSTOM = "custom"


class MembershipRole(StrEnum):
    ORGANIZATION_OWNER = "organization_owner"
    ORGANIZATION_ADMINISTRATOR = "organization_administrator"
    DEPARTMENT_ADMINISTRATOR = "department_administrator"
    INVESTIGATOR = "investigator"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class PluginScope(StrEnum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    DEPARTMENT = "department"


class BenchmarkScope(StrEnum):
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PRIVATE = "private"


class ResourceKind(StrEnum):
    CASE = "case"
    EVIDENCE_REF = "evidence_ref"
    WORKFLOW = "workflow"
    BENCHMARK = "benchmark"
    PLUGIN = "plugin"
    AUDIT = "audit"
    OPERATIONS = "operations"
    REPORT = "report"
    DATASET = "dataset"


# Membership role → ISPF permission role names (scoped; do not transfer across orgs).
MEMBERSHIP_TO_ISPF_ROLES: dict[MembershipRole, tuple[str, ...]] = {
    MembershipRole.ORGANIZATION_OWNER: ("administrator",),
    MembershipRole.ORGANIZATION_ADMINISTRATOR: ("supervisor",),
    MembershipRole.DEPARTMENT_ADMINISTRATOR: ("supervisor",),
    MembershipRole.INVESTIGATOR: ("investigator",),
    MembershipRole.REVIEWER: ("reviewer",),
    MembershipRole.OBSERVER: ("observer",),
}


@dataclass(frozen=True)
class ResourceOwnership:
    """Immutable ownership metadata for tenant-scoped resources."""

    organization_id: str
    department_id: str
    resource_owner: str
    classification: Classification
    creation_time: float
    resource_kind: ResourceKind
    resource_id: str

    def public_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "department_id": self.department_id,
            "resource_owner": self.resource_owner,
            "classification": self.classification.value,
            "creation_time": self.creation_time,
            "resource_kind": self.resource_kind.value,
            "resource_id": self.resource_id,
        }


@dataclass
class OrganizationConfig:
    feature_flags: dict[str, bool] = field(default_factory=dict)
    quotas: dict[str, int] = field(default_factory=dict)
    plugin_enablement: dict[str, bool] = field(default_factory=dict)
    workflow_availability: dict[str, bool] = field(default_factory=dict)
    benchmark_availability: dict[str, bool] = field(default_factory=dict)
    policy_overrides: dict[str, Any] = field(default_factory=dict)
    branding: dict[str, Any] = field(default_factory=dict)  # reserved

    def public_dict(self) -> dict[str, Any]:
        return {
            "feature_flags": dict(self.feature_flags),
            "quotas": dict(self.quotas),
            "plugin_enablement": dict(self.plugin_enablement),
            "workflow_availability": dict(self.workflow_availability),
            "benchmark_availability": dict(self.benchmark_availability),
            "policy_overrides": dict(self.policy_overrides),
            # branding reserved — never expose secrets; empty stub only
            "branding": {},
        }
