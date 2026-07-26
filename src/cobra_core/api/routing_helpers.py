"""Small helpers for public API resource catalogs."""

from __future__ import annotations

from typing import Any


def workflow_catalog_for_org(organization_id: str) -> list[dict[str, Any]]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.routing import TENANT_ROUTER

    org = ORGANIZATION_REGISTRY.get(organization_id)
    avail = dict(org.configuration.workflow_availability)
    if "default" not in avail:
        avail["default"] = True
    return [
        {
            "workflow_id": wid,
            "organization_id": organization_id,
            "available": TENANT_ROUTER.workflow_available(
                organization_id=organization_id, workflow_id=wid
            ),
            "scope": "organization",
        }
        for wid in sorted(avail)
    ]
