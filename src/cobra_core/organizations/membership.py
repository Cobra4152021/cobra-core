"""Scoped organization membership — roles do not transfer across orgs."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from cobra_core.organizations.schemas import MEMBERSHIP_TO_ISPF_ROLES, MembershipRole
from cobra_core.organizations.validation import (
    OrganizationValidationError,
    parse_membership_role,
    require_id,
)


@dataclass
class Membership:
    principal_id: str
    organization_id: str
    roles: list[MembershipRole]
    department_ids: list[str] = field(default_factory=list)
    created: float = field(default_factory=time.time)
    active: bool = True

    def ispf_roles(self) -> list[str]:
        out: list[str] = []
        for role in self.roles:
            out.extend(MEMBERSHIP_TO_ISPF_ROLES.get(role, ()))
        # stable unique
        seen: set[str] = set()
        ordered: list[str] = []
        for r in out:
            if r not in seen:
                seen.add(r)
                ordered.append(r)
        return ordered

    def public_dict(self) -> dict[str, Any]:
        return {
            "principal_id": self.principal_id,
            "organization_id": self.organization_id,
            "roles": [r.value for r in self.roles],
            "department_ids": list(self.department_ids),
            "created": self.created,
            "active": self.active,
        }


class MembershipRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # (principal_id, organization_id) → Membership
        self._members: dict[tuple[str, str], Membership] = {}

    def reset_for_tests(self) -> None:
        with self._lock:
            self._members.clear()

    def add(
        self,
        *,
        principal_id: str,
        organization_id: str,
        roles: list[str | MembershipRole],
        department_ids: list[str] | None = None,
    ) -> Membership:
        pid = require_id(principal_id, field="principal_id")
        oid = require_id(organization_id, field="organization_id")
        parsed = [parse_membership_role(r) for r in roles]
        if not parsed:
            raise OrganizationValidationError("invalid_membership_role", "roles required")
        m = Membership(
            principal_id=pid,
            organization_id=oid,
            roles=parsed,
            department_ids=[require_id(d, field="department_id") for d in (department_ids or [])],
        )
        with self._lock:
            self._members[(pid, oid)] = m
        return m

    def get(self, principal_id: str, organization_id: str) -> Membership:
        key = (principal_id.strip(), organization_id.strip())
        with self._lock:
            try:
                return self._members[key]
            except KeyError as exc:
                raise OrganizationValidationError(
                    "membership_not_found",
                    f"no membership for {principal_id} in {organization_id}",
                ) from exc

    def has_membership(self, principal_id: str, organization_id: str) -> bool:
        with self._lock:
            m = self._members.get((principal_id.strip(), organization_id.strip()))
            return bool(m and m.active)

    def list_for_org(self, organization_id: str) -> list[Membership]:
        oid = organization_id.strip()
        with self._lock:
            return sorted(
                (m for m in self._members.values() if m.organization_id == oid),
                key=lambda m: m.principal_id,
            )

    def list_for_principal(self, principal_id: str) -> list[Membership]:
        pid = principal_id.strip()
        with self._lock:
            return sorted(
                (m for m in self._members.values() if m.principal_id == pid),
                key=lambda m: m.organization_id,
            )

    def revoke(self, principal_id: str, organization_id: str) -> Membership:
        m = self.get(principal_id, organization_id)
        m.active = False
        with self._lock:
            self._members[(m.principal_id, m.organization_id)] = m
        return m


MEMBERSHIP_REGISTRY = MembershipRegistry()
