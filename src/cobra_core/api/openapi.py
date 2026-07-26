"""Deterministic OpenAPI 3.1 document for /api/v1."""

from __future__ import annotations

import json
from typing import Any

from cobra_core.api.versioning import ApiVersionInfo, version_prefix


def _path_item(summary: str, *, method: str = "get", body: bool = False) -> dict[str, Any]:
    op: dict[str, Any] = {
        "summary": summary,
        "security": [{"bearerAuth": []}],
        "responses": {
            "200": {"description": "Success"},
            "401": {"description": "Unauthenticated"},
            "403": {"description": "Forbidden"},
            "404": {"description": "Not found"},
            "429": {"description": "Rate limited"},
        },
    }
    if method == "get":
        op["parameters"] = [
            {
                "name": "limit",
                "in": "query",
                "schema": {"type": "integer", "minimum": 1, "maximum": 100},
            },
            {
                "name": "cursor",
                "in": "query",
                "schema": {"type": "string"},
            },
        ]
    if body:
        op["requestBody"] = {
            "required": False,
            "content": {
                "application/json": {
                    "schema": {"type": "object", "additionalProperties": True}
                }
            },
        }
    return {method: op}


def build_openapi_document() -> dict[str, Any]:
    """Build a deterministic OpenAPI 3.1 document (stable key order via json dumps)."""
    prefix = version_prefix("v1")
    info = ApiVersionInfo()
    paths: dict[str, Any] = {
        prefix + "/health": {
            "get": {
                "summary": "API health",
                "security": [],
                "responses": {"200": {"description": "Healthy"}},
            }
        },
        prefix + "/status": _path_item("API status and version info"),
        prefix + "/organizations": _path_item("List organizations"),
        prefix + "/organizations/{organization_id}": _path_item("Get organization"),
        prefix + "/cases": {
            **_path_item("List cases"),
            "post": _path_item("Create case", method="post", body=True)["post"],
        },
        prefix + "/cases/{case_id}": _path_item("Get case"),
        prefix + "/workflows": _path_item("List workflows"),
        prefix + "/workflows/{workflow_id}/run": _path_item(
            "Run workflow", method="post", body=True
        ),
        prefix + "/evidence": _path_item("List evidence references"),
        prefix + "/evidence/{evidence_id}": _path_item("Retrieve evidence reference"),
        prefix + "/plugins": _path_item("List plugins"),
        prefix + "/benchmark/datasets": _path_item("List benchmark datasets"),
        prefix + "/operations/status": _path_item("Operations status"),
        prefix + "/security/status": _path_item("Security status"),
        prefix + "/reports/{report_id}": _path_item("Get report"),
        prefix + "/openapi.json": {
            "get": {
                "summary": "OpenAPI 3.1 document",
                "security": [{"bearerAuth": []}],
                "responses": {"200": {"description": "OpenAPI document"}},
            }
        },
    }
    doc: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "Cobra Public API",
            "version": "1.0.0",
            "description": (
                "Stable public integration surface (PASF / KC-036). "
                + info.deprecation_policy
            ),
            "x-stability": info.stability,
            "x-supported-versions": list(info.supported),
        },
        "servers": [{"url": "/", "description": "Cobra Core"}],
        "paths": dict(sorted(paths.items())),
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "opaque",
                    "description": "ISPF Bearer token (API Client or Service principal)",
                }
            },
            "schemas": {
                "Error": {
                    "type": "object",
                    "required": [
                        "error_code",
                        "message",
                        "request_id",
                        "timestamp",
                        "documentation_url",
                    ],
                    "properties": {
                        "error_code": {"type": "string"},
                        "message": {"type": "string"},
                        "request_id": {"type": "string"},
                        "timestamp": {"type": "number"},
                        "documentation_url": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
                "Pagination": {
                    "type": "object",
                    "properties": {
                        "limit": {"type": "integer"},
                        "cursor": {"type": "string", "nullable": True},
                        "next_cursor": {"type": "string", "nullable": True},
                    },
                },
            },
        },
        "tags": [
            {"name": name}
            for name in [
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
            ]
        ],
    }
    # Round-trip through sorted JSON for deterministic output
    return json.loads(json.dumps(doc, sort_keys=True, separators=(",", ":")))


def render_openapi_json() -> str:
    return json.dumps(build_openapi_document(), sort_keys=True, indent=2) + "\n"
