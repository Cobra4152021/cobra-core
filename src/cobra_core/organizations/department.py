"""Department model — inherits organization policies unless overridden."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from cobra_core.organizations.organization import Organization
from cobra_core.organizations.schemas import DepartmentKind
from cobra_core.organizations.validation import (
    parse_department_kind,
    require_id,
    require_name,
)

BUILTIN_DEPARTMENT_KINDS: tuple[DepartmentKind, ...] = (
    DepartmentKind.SHERIFF,
    DepartmentKind.POLICE,
    DepartmentKind.COMPLIANCE,
    DepartmentKind.INTERNAL_AFFAIRS,
    DepartmentKind.UNION,
    DepartmentKind.INSPECTOR_GENERAL,
    DepartmentKind.RISK_MANAGEMENT,
)


@dataclass
class Department:
    department_id: str
    organization_id: str
    name: str
    kind: DepartmentKind
    created: float
    policy_overrides: dict[str, Any] = field(default_factory=dict)
    inherit_org_policies: bool = True

    def effective_policies(self, org: Organization) -> dict[str, Any]:
        base = dict(org.security_policies)
        if self.inherit_org_policies:
            merged = {**base, **dict(org.configuration.policy_overrides)}
        else:
            merged = {}
        merged.update(self.policy_overrides)
        return merged

    def public_dict(self) -> dict[str, Any]:
        return {
            "department_id": self.department_id,
            "organization_id": self.organization_id,
            "name": self.name,
            "kind": self.kind.value,
            "created": self.created,
            "inherit_org_policies": self.inherit_org_policies,
            "policy_overrides": dict(self.policy_overrides),
        }


def new_department(
    *,
    organization_id: str,
    name: str,
    kind: str | DepartmentKind,
    department_id: str | None = None,
    inherit_org_policies: bool = True,
    policy_overrides: dict[str, Any] | None = None,
) -> Department:
    return Department(
        department_id=require_id(
            department_id or f"dept_{uuid.uuid4().hex[:10]}",
            field="department_id",
        ),
        organization_id=require_id(organization_id, field="organization_id"),
        name=require_name(name),
        kind=parse_department_kind(kind),
        created=time.time(),
        policy_overrides=dict(policy_overrides or {}),
        inherit_org_policies=inherit_org_policies,
    )


def seed_builtin_departments(organization_id: str) -> list[Department]:
    out: list[Department] = []
    for kind in BUILTIN_DEPARTMENT_KINDS:
        out.append(
            new_department(
                organization_id=organization_id,
                name=kind.value.replace("_", " ").title(),
                kind=kind,
                department_id=f"dept_{organization_id}_{kind.value}",
            )
        )
    return out
