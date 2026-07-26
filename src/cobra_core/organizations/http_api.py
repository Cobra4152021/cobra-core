"""Authenticated organization HTTP handlers — no secrets exposed."""

from __future__ import annotations

from typing import Any

from cobra_core.organizations.audit import ORGANIZATION_AUDIT
from cobra_core.organizations.metrics import ORGANIZATION_METRICS
from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
from cobra_core.organizations.validation import OrganizationValidationError


def handle_organizations_list() -> dict[str, Any]:
    orgs = [o.public_dict() for o in ORGANIZATION_REGISTRY.list_organizations()]
    return {"ok": True, "organizations": orgs}


def handle_organization_get(organization_id: str) -> tuple[int, dict[str, Any]]:
    try:
        org = ORGANIZATION_REGISTRY.get(organization_id)
        return 200, {"ok": True, "organization": org.public_dict()}
    except OrganizationValidationError as exc:
        return 404, {"ok": False, "error": {"code": exc.code, "message": exc.message}}


def handle_organization_members(organization_id: str) -> tuple[int, dict[str, Any]]:
    try:
        ORGANIZATION_REGISTRY.get(organization_id)
        members = [
            m.public_dict()
            for m in ORGANIZATION_REGISTRY.membership.list_for_org(organization_id)
        ]
        return 200, {"ok": True, "organization_id": organization_id, "members": members}
    except OrganizationValidationError as exc:
        return 404, {"ok": False, "error": {"code": exc.code, "message": exc.message}}


def handle_organization_departments(organization_id: str) -> tuple[int, dict[str, Any]]:
    try:
        depts = [
            d.public_dict() for d in ORGANIZATION_REGISTRY.list_departments(organization_id)
        ]
        return 200, {
            "ok": True,
            "organization_id": organization_id,
            "departments": depts,
        }
    except OrganizationValidationError as exc:
        return 404, {"ok": False, "error": {"code": exc.code, "message": exc.message}}


def handle_organization_status(organization_id: str) -> tuple[int, dict[str, Any]]:
    try:
        org = ORGANIZATION_REGISTRY.get(organization_id)
        members = ORGANIZATION_REGISTRY.membership.list_for_org(organization_id)
        resources = ORGANIZATION_REGISTRY.resources_for_org(organization_id)
        return 200, {
            "ok": True,
            "organization_id": org.organization_id,
            "status": org.status.value,
            "classification": org.classification.value,
            "member_count": len(members),
            "department_count": len(ORGANIZATION_REGISTRY.list_departments(organization_id)),
            "resource_count": len(resources),
            "policy_version": org.security_policies.get("policy_version", "motf-1"),
        }
    except OrganizationValidationError as exc:
        return 404, {"ok": False, "error": {"code": exc.code, "message": exc.message}}


def handle_organization_metrics(organization_id: str) -> tuple[int, dict[str, Any]]:
    try:
        ORGANIZATION_REGISTRY.get(organization_id)
        # Refresh user count from membership
        users = len(ORGANIZATION_REGISTRY.membership.list_for_org(organization_id))
        cases = len(
            [
                r
                for r in ORGANIZATION_REGISTRY.resources_for_org(organization_id)
                if r.resource_kind.value == "case"
            ]
        )
        ORGANIZATION_METRICS.set_counts(organization_id, users=users, cases=cases)
        return 200, {
            "ok": True,
            "metrics": ORGANIZATION_METRICS.snapshot(organization_id),
            "audit_recent": ORGANIZATION_AUDIT.for_organization(organization_id, limit=10),
        }
    except OrganizationValidationError as exc:
        return 404, {"ok": False, "error": {"code": exc.code, "message": exc.message}}
