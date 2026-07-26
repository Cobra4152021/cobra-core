"""Plugin manifest parsing and normalization."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.schemas import PluginType

REQUIRED_FIELDS = (
    "plugin_id",
    "name",
    "version",
    "author",
    "description",
    "license",
    "supported_core_version",
    "plugin_type",
    "entry_point",
    "required_permissions",
)


def load_manifest_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PluginError(PluginErrorCode.MANIFEST_INVALID, f"manifest missing: {path}")
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PluginError(PluginErrorCode.MANIFEST_INVALID, f"invalid JSON: {exc}") from exc
    if not isinstance(raw, dict):
        raise PluginError(PluginErrorCode.MANIFEST_INVALID, "manifest must be an object")
    return normalize_manifest(raw)


def normalize_manifest(raw: dict[str, Any]) -> dict[str, Any]:
    missing = [f for f in REQUIRED_FIELDS if f not in raw or raw[f] in (None, "")]
    if missing:
        raise PluginError(
            PluginErrorCode.MANIFEST_INVALID,
            f"missing required fields: {', '.join(missing)}",
        )
    plugin_id = str(raw["plugin_id"]).strip()
    if not plugin_id or "/" in plugin_id or "\\" in plugin_id:
        raise PluginError(PluginErrorCode.MANIFEST_INVALID, "invalid plugin_id")
    try:
        ptype = PluginType(str(raw["plugin_type"]).strip())
    except ValueError as exc:
        raise PluginError(
            PluginErrorCode.TYPE_UNSUPPORTED,
            f"unsupported plugin_type: {raw.get('plugin_type')!r}",
        ) from exc
    perms = raw.get("required_permissions")
    if not isinstance(perms, list) or not perms:
        raise PluginError(
            PluginErrorCode.MANIFEST_INVALID,
            "required_permissions must be a non-empty list",
        )
    deps = raw.get("dependencies") or []
    if not isinstance(deps, list):
        raise PluginError(PluginErrorCode.MANIFEST_INVALID, "dependencies must be a list")
    return {
        "plugin_id": plugin_id,
        "name": str(raw["name"]).strip(),
        "version": str(raw["version"]).strip(),
        "author": str(raw["author"]).strip(),
        "description": str(raw["description"]).strip(),
        "license": str(raw["license"]).strip(),
        "supported_core_version": str(raw["supported_core_version"]).strip(),
        "plugin_type": ptype.value,
        "entry_point": str(raw["entry_point"]).strip(),
        "required_permissions": [str(p).strip() for p in perms],
        "dependencies": [str(d).strip() for d in deps if str(d).strip()],
        "checksum": str(raw.get("checksum") or "").strip(),
        "signature": str(raw.get("signature") or "").strip(),  # reserved
        "min_core_version": str(raw.get("min_core_version") or "").strip(),
        "max_core_version": str(raw.get("max_core_version") or "").strip(),
        "required_apis": [str(a).strip() for a in (raw.get("required_apis") or [])],
        "schema_version": str(raw.get("schema_version") or "1").strip(),
    }
