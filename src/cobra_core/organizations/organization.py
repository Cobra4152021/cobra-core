"""Organization model and lifecycle."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from cobra_core.organizations.schemas import (
    Classification,
    OrganizationConfig,
    OrganizationStatus,
)
from cobra_core.organizations.validation import (
    OrganizationValidationError,
    parse_classification,
    require_id,
    require_name,
)


@dataclass
class Organization:
    organization_id: str
    name: str
    status: OrganizationStatus
    classification: Classification
    created: float
    owner: str
    configuration: OrganizationConfig = field(default_factory=OrganizationConfig)
    security_policies: dict[str, Any] = field(default_factory=dict)
    quota: dict[str, int] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "status": self.status.value,
            "classification": self.classification.value,
            "created": self.created,
            "owner": self.owner,
            "configuration": self.configuration.public_dict(),
            "security_policies": {
                k: v
                for k, v in self.security_policies.items()
                if str(k).lower()
                not in {"secret", "token", "api_key", "password", "credential"}
            },
            "quota": dict(self.quota or self.configuration.quotas),
            # branding reserved — not exposed
        }


def new_organization(
    *,
    name: str,
    owner: str,
    organization_id: str | None = None,
    classification: str | Classification = Classification.INTERNAL,
    feature_flags: dict[str, bool] | None = None,
    quotas: dict[str, int] | None = None,
) -> Organization:
    oid = require_id(
        organization_id or f"org_{uuid.uuid4().hex[:12]}",
        field="organization_id",
    )
    owner_id = require_id(owner, field="owner")
    cfg = OrganizationConfig(
        feature_flags=dict(feature_flags or {"cases": True, "workflows": True, "plugins": True}),
        quotas=dict(
            quotas
            or {
                "cases_per_day": 1000,
                "workflows_per_day": 1000,
                "users": 500,
                "storage_mb": 10240,
            }
        ),
        plugin_enablement={},
        workflow_availability={"default": True},
        benchmark_availability={"global": True},
        policy_overrides={},
        branding={},
    )
    return Organization(
        organization_id=oid,
        name=require_name(name),
        status=OrganizationStatus.ACTIVE,
        classification=parse_classification(classification),
        created=time.time(),
        owner=owner_id,
        configuration=cfg,
        security_policies={"policy_version": "motf-1", "inherit": True},
        quota=dict(cfg.quotas),
    )


def assert_org_active(org: Organization) -> None:
    if org.status != OrganizationStatus.ACTIVE:
        raise OrganizationValidationError(
            "org_inactive",
            f"organization not active: {org.organization_id} ({org.status.value})",
        )
