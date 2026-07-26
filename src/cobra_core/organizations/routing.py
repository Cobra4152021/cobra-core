"""Tenant routing helpers — scope resolution without changing AIR/ISF AI behavior."""

from __future__ import annotations

from typing import Any

from cobra_core.organizations.registry import (
    ORGANIZATION_REGISTRY,
    OrganizationRegistry,
    benchmark_visible,
    plugin_visible,
)
from cobra_core.organizations.schemas import BenchmarkScope, PluginScope
from cobra_core.organizations.tenancy import TENANCY, TenancyService


class TenantRouter:
    """Resolves whether scoped assets are visible inside a tenant context."""

    def __init__(
        self,
        *,
        registry: OrganizationRegistry | None = None,
        tenancy: TenancyService | None = None,
    ) -> None:
        self.registry = registry if registry is not None else ORGANIZATION_REGISTRY
        self.tenancy = tenancy if tenancy is not None else TENANCY

    def visible_plugins(
        self,
        *,
        principal_id: str,
        organization_id: str,
        department_id: str = "",
        catalog: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        self.tenancy.resolve_context(
            principal_id=principal_id,
            organization_id=organization_id,
            department_id=department_id,
        )
        out: list[dict[str, Any]] = []
        for item in catalog:
            if plugin_visible(
                plugin_scope=str(item.get("scope") or PluginScope.ORGANIZATION.value),
                plugin_org_id=str(item.get("organization_id") or ""),
                plugin_dept_id=str(item.get("department_id") or ""),
                viewer_org_id=organization_id,
                viewer_dept_id=department_id,
            ):
                out.append(item)
        return out

    def visible_benchmarks(
        self,
        *,
        principal_id: str,
        organization_id: str,
        catalog: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        self.tenancy.resolve_context(
            principal_id=principal_id,
            organization_id=organization_id,
        )
        out: list[dict[str, Any]] = []
        for item in catalog:
            if benchmark_visible(
                scope=str(item.get("scope") or BenchmarkScope.ORGANIZATION.value),
                dataset_org_id=str(item.get("organization_id") or ""),
                dataset_owner=str(item.get("owner") or ""),
                viewer_org_id=organization_id,
                viewer_principal_id=principal_id,
            ):
                # Org config may disable a benchmark id
                org = self.registry.get(organization_id)
                bid = str(item.get("dataset_id") or item.get("id") or "")
                avail = org.configuration.benchmark_availability
                if bid and bid in avail and not avail[bid]:
                    continue
                out.append(item)
        return out

    def workflow_available(self, *, organization_id: str, workflow_id: str) -> bool:
        org = self.registry.get(organization_id)
        avail = org.configuration.workflow_availability
        if workflow_id in avail:
            return bool(avail[workflow_id])
        return bool(avail.get("default", True))


TENANT_ROUTER = TenantRouter()
