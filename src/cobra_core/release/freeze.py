"""Feature freeze locks for RC1 — schemas and public surfaces."""

from __future__ import annotations

from typing import Any

RC1_FROZEN_SURFACES: tuple[str, ...] = (
    "protocol_v1",
    "public_api_v1",
    "plugin_manifests",
    "organization_schema",
    "security_schema",
    "workflow_schema",
    "case_schema",
    "benchmark_schema",
    "evidence_schema",
)

FREEZE_POLICY = (
    "KC-038 feature freeze: only compatibility bug fixes allowed. "
    "Breaking changes require a new major/RC train. "
    "Production enablement remains disabled."
)


def freeze_manifest() -> dict[str, Any]:
    from cobra_core.api.openapi import build_openapi_document
    from cobra_core.api.versioning import ApiVersionInfo
    from cobra_core.production.integrity import (
        openapi_checksum,
        organization_metadata_checksum,
        policy_checksum,
    )

    return {
        "version": "v1.0.0-rc1",
        "frozen_surfaces": list(RC1_FROZEN_SURFACES),
        "policy": FREEZE_POLICY,
        "api": ApiVersionInfo().public_dict(),
        "openapi_info_version": build_openapi_document()["info"]["version"],
        "checksums": {
            "openapi": openapi_checksum(),
            "policy": policy_checksum(),
            "organization_metadata": organization_metadata_checksum(),
        },
        "production_enabled": False,
    }
