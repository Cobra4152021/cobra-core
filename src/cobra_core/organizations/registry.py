"""Organization + department registry and tenant resource index."""

from __future__ import annotations

import threading
import time
from typing import Any

from cobra_core.organizations.department import Department, seed_builtin_departments
from cobra_core.organizations.membership import MEMBERSHIP_REGISTRY, MembershipRegistry
from cobra_core.organizations.organization import Organization, assert_org_active, new_organization
from cobra_core.organizations.schemas import (
    BenchmarkScope,
    Classification,
    PluginScope,
    ResourceKind,
    ResourceOwnership,
)
from cobra_core.organizations.validation import OrganizationValidationError, require_id


class OrganizationRegistry:
    def __init__(self, *, membership: MembershipRegistry | None = None) -> None:
        self._lock = threading.Lock()
        self._orgs: dict[str, Organization] = {}
        self._departments: dict[str, Department] = {}  # department_id → dept
        self._ownership: dict[str, ResourceOwnership] = {}  # resource_key → ownership
        self.membership = membership if membership is not None else MEMBERSHIP_REGISTRY

    def reset_for_tests(self) -> None:
        with self._lock:
            self._orgs.clear()
            self._departments.clear()
            self._ownership.clear()
        self.membership.reset_for_tests()

    def create_organization(
        self,
        *,
        name: str,
        owner: str,
        organization_id: str | None = None,
        seed_departments: bool = True,
        **kwargs: Any,
    ) -> Organization:
        org = new_organization(
            name=name,
            owner=owner,
            organization_id=organization_id,
            **kwargs,
        )
        with self._lock:
            if org.organization_id in self._orgs:
                raise OrganizationValidationError(
                    "duplicate_org", f"organization exists: {org.organization_id}"
                )
            self._orgs[org.organization_id] = org
        # Owner membership
        self.membership.add(
            principal_id=owner,
            organization_id=org.organization_id,
            roles=["organization_owner"],
        )
        if seed_departments:
            for dept in seed_builtin_departments(org.organization_id):
                self.add_department(dept)
        return org

    def get(self, organization_id: str) -> Organization:
        with self._lock:
            try:
                return self._orgs[organization_id.strip()]
            except KeyError as exc:
                raise OrganizationValidationError(
                    "org_not_found", f"organization not found: {organization_id}"
                ) from exc

    def list_organizations(self) -> list[Organization]:
        with self._lock:
            return [self._orgs[k] for k in sorted(self._orgs)]

    def add_department(self, department: Department) -> Department:
        self.get(department.organization_id)  # must exist
        with self._lock:
            self._departments[department.department_id] = department
        return department

    def get_department(self, department_id: str) -> Department:
        with self._lock:
            try:
                return self._departments[department_id.strip()]
            except KeyError as exc:
                raise OrganizationValidationError(
                    "dept_not_found", f"department not found: {department_id}"
                ) from exc

    def list_departments(self, organization_id: str) -> list[Department]:
        oid = organization_id.strip()
        self.get(oid)
        with self._lock:
            return sorted(
                (d for d in self._departments.values() if d.organization_id == oid),
                key=lambda d: d.department_id,
            )

    def tag_resource(
        self,
        *,
        organization_id: str,
        resource_kind: ResourceKind | str,
        resource_id: str,
        resource_owner: str,
        department_id: str = "",
        classification: Classification | str | None = None,
    ) -> ResourceOwnership:
        org = self.get(organization_id)
        assert_org_active(org)
        kind = (
            resource_kind
            if isinstance(resource_kind, ResourceKind)
            else ResourceKind(str(resource_kind))
        )
        rid = require_id(resource_id, field="resource_id")
        key = f"{kind.value}:{rid}"
        with self._lock:
            if key in self._ownership:
                # Immutable — reject mutation
                raise OrganizationValidationError(
                    "ownership_immutable",
                    f"ownership already set for {key}",
                )
            if department_id:
                dept = self._departments.get(department_id.strip())
                if not dept or dept.organization_id != org.organization_id:
                    raise OrganizationValidationError(
                        "dept_mismatch",
                        "department not in organization",
                    )
            ownership = ResourceOwnership(
                organization_id=org.organization_id,
                department_id=(department_id or "").strip(),
                resource_owner=require_id(resource_owner, field="resource_owner"),
                classification=(
                    classification
                    if isinstance(classification, Classification)
                    else org.classification
                ),
                creation_time=time.time(),
                resource_kind=kind,
                resource_id=rid,
            )
            self._ownership[key] = ownership
            return ownership

    def ownership_of(self, resource_kind: ResourceKind | str, resource_id: str) -> ResourceOwnership:
        kind = (
            resource_kind
            if isinstance(resource_kind, ResourceKind)
            else ResourceKind(str(resource_kind))
        )
        key = f"{kind.value}:{resource_id.strip()}"
        with self._lock:
            try:
                return self._ownership[key]
            except KeyError as exc:
                raise OrganizationValidationError(
                    "ownership_not_found", f"no ownership for {key}"
                ) from exc

    def resources_for_org(self, organization_id: str) -> list[ResourceOwnership]:
        oid = organization_id.strip()
        with self._lock:
            return sorted(
                (o for o in self._ownership.values() if o.organization_id == oid),
                key=lambda o: (o.resource_kind.value, o.resource_id),
            )


ORGANIZATION_REGISTRY = OrganizationRegistry()


def plugin_visible(
    *,
    plugin_scope: PluginScope | str,
    plugin_org_id: str,
    plugin_dept_id: str,
    viewer_org_id: str,
    viewer_dept_id: str = "",
) -> bool:
    scope = PluginScope(plugin_scope) if not isinstance(plugin_scope, PluginScope) else plugin_scope
    if scope == PluginScope.GLOBAL:
        return True
    if scope == PluginScope.ORGANIZATION:
        return plugin_org_id == viewer_org_id
    if scope == PluginScope.DEPARTMENT:
        return plugin_org_id == viewer_org_id and plugin_dept_id == viewer_dept_id
    return False


def benchmark_visible(
    *,
    scope: BenchmarkScope | str,
    dataset_org_id: str,
    dataset_owner: str,
    viewer_org_id: str,
    viewer_principal_id: str,
) -> bool:
    s = BenchmarkScope(scope) if not isinstance(scope, BenchmarkScope) else scope
    if s == BenchmarkScope.GLOBAL:
        return True
    if s == BenchmarkScope.ORGANIZATION:
        return dataset_org_id == viewer_org_id
    if s == BenchmarkScope.PRIVATE:
        return dataset_org_id == viewer_org_id and dataset_owner == viewer_principal_id
    return False
