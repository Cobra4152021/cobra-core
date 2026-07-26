"""Fail-closed plugin validation (manifest, compat, checksum, namespace)."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from cobra_core.plugins.config import PluginConfig
from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.permissions import parse_permissions, require_type_permission
from cobra_core.plugins.schemas import PluginType

_SEMVER = re.compile(
    r"^v?(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)(?P<pre>[0-9A-Za-z.\-]*)?$"
)


def _parse_ver(value: str) -> tuple[int, int, int, str]:
    m = _SEMVER.match((value or "").strip())
    if not m:
        raise PluginError(PluginErrorCode.COMPATIBILITY_FAILED, f"bad version: {value!r}")
    return int(m["major"]), int(m["minor"]), int(m["patch"]), m["pre"] or ""


def _cmp(a: tuple[int, int, int, str], b: tuple[int, int, int, str]) -> int:
    for x, y in zip(a[:3], b[:3], strict=True):
        if x != y:
            return -1 if x < y else 1
    # ignore pre for compatibility gates
    return 0


def compute_checksum(manifest_path: Path, entry_module_file: Path | None) -> str:
    h = hashlib.sha256()
    h.update(manifest_path.read_bytes())
    if entry_module_file and entry_module_file.is_file():
        h.update(entry_module_file.read_bytes())
    return h.hexdigest()


def validate_manifest(
    manifest: dict[str, Any],
    *,
    config: PluginConfig,
    manifest_path: Path | None = None,
    entry_file: Path | None = None,
    known_ids: set[str] | None = None,
) -> None:
    plugin_id = str(manifest["plugin_id"])
    for reserved in config.reserved_namespaces:
        if plugin_id.startswith(reserved):
            raise PluginError(
                PluginErrorCode.RESERVED_NAMESPACE,
                f"plugin_id uses reserved namespace: {reserved}",
            )
    if known_ids and plugin_id in known_ids:
        raise PluginError(PluginErrorCode.DUPLICATE_ID, f"duplicate plugin_id: {plugin_id}")

    ptype = PluginType(manifest["plugin_type"])
    granted = parse_permissions(list(manifest["required_permissions"]))
    require_type_permission(ptype, granted)

    entry = str(manifest["entry_point"])
    if not any(entry.startswith(p) for p in config.allowed_entry_prefixes):
        raise PluginError(
            PluginErrorCode.VALIDATION_FAILED,
            f"entry_point outside allowed prefixes: {entry}",
        )
    if ".." in entry or entry.startswith("/") or "\\" in entry:
        raise PluginError(PluginErrorCode.VALIDATION_FAILED, "unsafe entry_point")

    # Compatibility
    core = _parse_ver(config.core_version)
    supported = str(manifest.get("supported_core_version") or "").strip()
    # supported_core_version may be "0.9.x" style or exact; accept major.minor match prefix.
    if supported.endswith(".x"):
        base = supported[:-2]
        if not config.core_version.startswith(base) and not config.core_version.startswith(
            base.replace("v", "")
        ):
            # also allow 0.9.0rc1 vs 0.9.x
            maj_min = ".".join(config.core_version.lstrip("v").split(".")[:2])
            if not supported.startswith(maj_min):
                raise PluginError(
                    PluginErrorCode.COMPATIBILITY_FAILED,
                    f"core {config.core_version} incompatible with {supported}",
                )
    else:
        try:
            _parse_ver(supported)
        except PluginError:
            # allow bare "0.9" as major.minor
            if not config.core_version.startswith(supported.lstrip("v")):
                raise PluginError(
                    PluginErrorCode.COMPATIBILITY_FAILED,
                    f"core {config.core_version} incompatible with {supported}",
                ) from None

    min_v = str(manifest.get("min_core_version") or "").strip()
    max_v = str(manifest.get("max_core_version") or "").strip()
    if min_v and _cmp(core, _parse_ver(min_v)) < 0:
        raise PluginError(
            PluginErrorCode.COMPATIBILITY_FAILED,
            f"core below min_core_version {min_v}",
        )
    if max_v and _cmp(core, _parse_ver(max_v)) > 0:
        raise PluginError(
            PluginErrorCode.COMPATIBILITY_FAILED,
            f"core above max_core_version {max_v}",
        )

    # required_apis — only known PEF APIs for now
    known_apis = {"pef.extension_v1", "pef.manifest_v1"}
    for api in manifest.get("required_apis") or []:
        if api not in known_apis:
            raise PluginError(
                PluginErrorCode.COMPATIBILITY_FAILED,
                f"required API unavailable: {api}",
            )

    declared = str(manifest.get("checksum") or "").strip()
    if declared and manifest_path is not None:
        actual = compute_checksum(manifest_path, entry_file)
        if actual != declared:
            raise PluginError(
                PluginErrorCode.CHECKSUM_MISMATCH,
                "manifest checksum mismatch",
            )
