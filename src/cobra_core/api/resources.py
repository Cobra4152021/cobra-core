"""Public API resource handlers — wrap existing Core subsystems under /api/v1."""

from __future__ import annotations

import time
import uuid
from typing import Any
from urllib.parse import parse_qs

from cobra_core.api.errors import ApiError, ApiErrorCode
from cobra_core.api.pagination import paginate, parse_limit
from cobra_core.api.validation import optional_str, require_object, require_str
from cobra_core.api.versioning import ApiVersionInfo
from cobra_core.api.webhooks import webhook_catalog


def _qs(query: str) -> dict[str, list[str]]:
    return parse_qs(query or "", keep_blank_values=False)


def _first(qs: dict[str, list[str]], key: str, default: str = "") -> str:
    vals = qs.get(key) or []
    return vals[0] if vals else default


def handle_health() -> dict[str, Any]:
    return {
        "ok": True,
        "status": "healthy",
        "api": "pasf",
        "version": "v1",
        "ts": time.time(),
    }


def handle_status() -> dict[str, Any]:
    info = ApiVersionInfo()
    return {
        "ok": True,
        "framework": "pasf",
        "version": info.public_dict(),
        "resource_groups": [
            "organizations",
            "cases",
            "workflows",
            "evidence",
            "plugins",
            "benchmark",
            "operations",
            "security",
            "health",
            "status",
        ],
        "webhooks": webhook_catalog(),
    }


def handle_organizations_list(*, query: str = "", organization_id: str = "") -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    if not organization_id:
        raise ApiError(ApiErrorCode.FORBIDDEN, "organization scope required", status=403)
    items = [ORGANIZATION_REGISTRY.get(organization_id).public_dict()]
    page = paginate(items, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_organization_get(org_id: str) -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.validation import OrganizationValidationError

    try:
        org = ORGANIZATION_REGISTRY.get(org_id)
    except OrganizationValidationError as exc:
        raise ApiError(ApiErrorCode.NOT_FOUND, exc.message, status=404) from exc
    return {"ok": True, "organization": org.public_dict()}


def handle_cases_list(*, query: str = "", organization_id: str = "") -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.schemas import ResourceKind

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    org = organization_id or _first(qs, "organization_id")
    items: list[dict[str, Any]] = []
    orgs = [ORGANIZATION_REGISTRY.get(org)] if org else ORGANIZATION_REGISTRY.list_organizations()
    for o in orgs:
        items.extend(
            r.public_dict()
            for r in ORGANIZATION_REGISTRY.resources_for_org(o.organization_id)
            if r.resource_kind == ResourceKind.CASE
        )
    page = paginate(items, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_case_get(
    case_id: str,
    *,
    principal_id: str,
    organization_id: str,
) -> dict[str, Any]:
    from cobra_core.organizations.schemas import ResourceKind
    from cobra_core.organizations.tenancy import TENANCY
    from cobra_core.organizations.validation import OrganizationValidationError

    try:
        ownership = TENANCY.assert_resource_access(
            principal_id=principal_id,
            organization_id=organization_id,
            resource_kind=ResourceKind.CASE,
            resource_id=case_id,
        )
    except OrganizationValidationError as exc:
        raise ApiError(ApiErrorCode.FORBIDDEN, exc.message, status=403) from exc
    return {"ok": True, "case": ownership.public_dict()}


def handle_case_create(
    payload: dict[str, Any] | None,
    *,
    principal_id: str,
    organization_id: str,
) -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.schemas import ResourceKind
    from cobra_core.organizations.validation import OrganizationValidationError
    from cobra_core.security import authorize
    from cobra_core.security.schemas import ResourceType

    body = require_object(payload or {})
    org_id = organization_id or require_str(body, "organization_id")
    department_id = optional_str(body, "department_id")
    case_id = optional_str(body, "case_id") or f"case_{uuid.uuid4().hex[:12]}"
    decision = authorize(
        principal_id=principal_id,
        action="create_case",
        resource_type=ResourceType.CASE,
        resource_id=case_id,
        attributes={"organization_id": org_id},
        organization_id=org_id,
        department_id=department_id,
    )
    if not decision.allowed():
        raise ApiError(
            ApiErrorCode.FORBIDDEN,
            decision.reason,
            status=403,
            details={"audit_ref": decision.audit_ref, "policy_id": decision.policy_id},
        )
    try:
        ownership = ORGANIZATION_REGISTRY.tag_resource(
            organization_id=org_id,
            resource_kind=ResourceKind.CASE,
            resource_id=case_id,
            resource_owner=principal_id,
            department_id=department_id,
        )
    except OrganizationValidationError as exc:
        raise ApiError(ApiErrorCode.CONFLICT, exc.message, status=409) from exc
    return {
        "ok": True,
        "case": ownership.public_dict(),
        "authorization": decision.audit_ref,
    }


def handle_workflows_list(*, query: str = "", organization_id: str = "") -> dict[str, Any]:
    from cobra_core.api.routing_helpers import workflow_catalog_for_org
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    org = organization_id or _first(qs, "organization_id")
    if org:
        ORGANIZATION_REGISTRY.get(org)  # validate exists
        items = workflow_catalog_for_org(org)
    else:
        items = [{"workflow_id": "default", "scope": "global", "available": True}]
    page = paginate(items, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_workflow_run(
    workflow_id: str,
    payload: dict[str, Any] | None,
    *,
    principal_id: str,
    organization_id: str,
) -> dict[str, Any]:
    from cobra_core.organizations.routing import TENANT_ROUTER
    from cobra_core.security import authorize
    from cobra_core.security.schemas import ResourceType

    body = require_object(payload or {})
    org_id = organization_id or require_str(body, "organization_id")
    if not TENANT_ROUTER.workflow_available(organization_id=org_id, workflow_id=workflow_id):
        raise ApiError(
            ApiErrorCode.FORBIDDEN, "workflow not available for organization", status=403
        )
    decision = authorize(
        principal_id=principal_id,
        action="run_workflow",
        resource_type=ResourceType.WORKFLOW,
        resource_id=workflow_id,
        attributes={"organization_id": org_id},
        organization_id=org_id,
    )
    if not decision.allowed():
        raise ApiError(
            ApiErrorCode.FORBIDDEN,
            decision.reason,
            status=403,
            details={"audit_ref": decision.audit_ref},
        )
    run_id = f"wfrun_{uuid.uuid4().hex[:12]}"
    return {
        "ok": True,
        "run": {
            "run_id": run_id,
            "workflow_id": workflow_id,
            "organization_id": org_id,
            "status": "accepted",
        },
        "authorization": decision.audit_ref,
    }


def handle_evidence_list(*, query: str = "", organization_id: str = "") -> dict[str, Any]:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY
    from cobra_core.organizations.schemas import ResourceKind

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    org = organization_id or _first(qs, "organization_id")
    items: list[dict[str, Any]] = []
    orgs = [ORGANIZATION_REGISTRY.get(org)] if org else ORGANIZATION_REGISTRY.list_organizations()
    for o in orgs:
        items.extend(
            r.public_dict()
            for r in ORGANIZATION_REGISTRY.resources_for_org(o.organization_id)
            if r.resource_kind == ResourceKind.EVIDENCE_REF
        )
    page = paginate(items, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_evidence_get(
    evidence_id: str,
    *,
    principal_id: str,
    organization_id: str,
) -> dict[str, Any]:
    from cobra_core.organizations.schemas import ResourceKind
    from cobra_core.organizations.tenancy import TENANCY
    from cobra_core.organizations.validation import OrganizationValidationError
    from cobra_core.security import authorize
    from cobra_core.security.schemas import ResourceType

    try:
        ownership = TENANCY.assert_resource_access(
            principal_id=principal_id,
            organization_id=organization_id,
            resource_kind=ResourceKind.EVIDENCE_REF,
            resource_id=evidence_id,
        )
    except OrganizationValidationError as exc:
        raise ApiError(ApiErrorCode.FORBIDDEN, exc.message, status=403) from exc
    org_id = organization_id
    decision = authorize(
        principal_id=principal_id,
        action="retrieve_evidence",
        resource_type=ResourceType.EVIDENCE,
        resource_id=evidence_id,
        attributes={"organization_id": org_id},
        organization_id=org_id,
        department_id=ownership.department_id,
    )
    if not decision.allowed():
        raise ApiError(
            ApiErrorCode.FORBIDDEN,
            decision.reason,
            status=403,
            details={"audit_ref": decision.audit_ref},
        )
    return {
        "ok": True,
        "evidence": ownership.public_dict(),
        "authorization": decision.audit_ref,
    }


def handle_plugins_list(*, query: str = "") -> dict[str, Any]:
    from cobra_core.plugins.manager import PLUGIN_MANAGER

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    PLUGIN_MANAGER.ensure_bootstrapped()
    items = PLUGIN_MANAGER.list_plugins()
    page = paginate(items, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_benchmark_datasets(*, query: str = "") -> dict[str, Any]:
    from cobra_core.benchmark.datasets.builtin import register_builtin_datasets
    from cobra_core.benchmark.registry import DATASET_REGISTRY

    qs = _qs(query)
    limit = parse_limit(_first(qs, "limit") or None)
    cursor = _first(qs, "cursor") or None
    if not DATASET_REGISTRY.list_ids():
        register_builtin_datasets()
    norm = [
        {
            "dataset_id": d.dataset_id,
            "version": d.version,
            "skill_id": d.skill_id,
            "title": d.title,
            "scope": "global",
            "case_count": len(d.cases),
        }
        for d in DATASET_REGISTRY.list_datasets()
    ]
    page = paginate(norm, limit=limit, cursor=cursor)
    return {"ok": True, **page.public_dict()}


def handle_operations_status() -> dict[str, Any]:
    from cobra_core.operations.http_api import handle_operations_status as _ops

    return {"ok": True, "operations": _ops()}


def handle_security_status() -> dict[str, Any]:
    from cobra_core.security.http_api import handle_security_status as _sec

    return {"ok": True, "security": _sec()}


def handle_report_get(report_id: str) -> dict[str, Any]:
    """Reference report surface (plugin report extensions)."""
    from cobra_core.plugins.manager import PLUGIN_MANAGER
    from cobra_core.plugins.schemas import PluginType

    PLUGIN_MANAGER.ensure_bootstrapped()
    for ext in PLUGIN_MANAGER.registry.extensions_by_type(PluginType.REPORT):
        payload = ext.payload
        if str(payload.get("report_id") or ext.extension_id) == report_id:
            return {"ok": True, "report": payload}
    raise ApiError(ApiErrorCode.NOT_FOUND, f"report not found: {report_id}", status=404)
