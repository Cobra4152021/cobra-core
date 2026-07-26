"""Integrity checks — config hashes, plugins, OpenAPI, policies, org metadata."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def configuration_hash(env: dict[str, str] | None = None) -> str:
    import os

    e = env if env is not None else dict(os.environ)
    # Only non-secret keys — never hash raw secrets into reports as plaintext values.
    keys = sorted(
        k
        for k in e
        if not any(s in k.lower() for s in ("secret", "token", "password", "api_key"))
    )
    payload = {k: e.get(k, "") for k in keys}
    return _sha256_text(json.dumps(payload, sort_keys=True, separators=(",", ":")))


def openapi_checksum() -> str:
    from cobra_core.api.openapi import render_openapi_json

    return _sha256_text(render_openapi_json())


def plugin_manifest_checksums() -> dict[str, str]:
    from cobra_core.plugins.manager import PLUGIN_MANAGER

    PLUGIN_MANAGER.ensure_bootstrapped()
    out: dict[str, str] = {}
    for rec in PLUGIN_MANAGER.registry.list_plugins():
        out[rec.plugin_id] = _sha256_text(
            json.dumps(rec.manifest, sort_keys=True, separators=(",", ":"))
        )
    return out


def policy_checksum() -> str:
    from cobra_core.security.policy import POLICY_ENGINE

    docs = POLICY_ENGINE.list_policies()
    return _sha256_text(json.dumps(docs, sort_keys=True, separators=(",", ":")))


def organization_metadata_checksum() -> str:
    from cobra_core.organizations.registry import ORGANIZATION_REGISTRY

    orgs = [o.public_dict() for o in ORGANIZATION_REGISTRY.list_organizations()]
    return _sha256_text(json.dumps(orgs, sort_keys=True, separators=(",", ":")))


def integrity_report() -> dict[str, Any]:
    return {
        "ok": True,
        "configuration_hash": configuration_hash(),
        "openapi_checksum": openapi_checksum(),
        "policy_checksum": policy_checksum(),
        "organization_metadata_checksum": organization_metadata_checksum(),
        "plugin_manifests": plugin_manifest_checksums(),
    }
