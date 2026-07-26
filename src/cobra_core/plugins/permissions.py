"""Explicit plugin permission checks."""

from __future__ import annotations

from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.schemas import TYPE_PERMISSIONS, Permission, PluginType


def parse_permissions(raw: list[str]) -> set[Permission]:
    out: set[Permission] = set()
    for item in raw:
        try:
            out.add(Permission(str(item).strip()))
        except ValueError as exc:
            raise PluginError(
                PluginErrorCode.PERMISSION_DENIED,
                f"unknown permission: {item!r}",
            ) from exc
    return out


def require_type_permission(plugin_type: PluginType, granted: set[Permission]) -> None:
    needed = TYPE_PERMISSIONS.get(plugin_type)
    if needed is None:
        raise PluginError(
            PluginErrorCode.TYPE_UNSUPPORTED,
            f"no permission mapping for type {plugin_type.value}",
        )
    if needed not in granted:
        raise PluginError(
            PluginErrorCode.PERMISSION_DENIED,
            f"plugin_type {plugin_type.value} requires permission {needed.value}",
        )


def assert_permissions_allowed(requested: set[Permission], allowed: set[Permission]) -> None:
    """Fail closed if any requested permission is outside the allowed grant set."""
    denied = requested - allowed
    if denied:
        names = ", ".join(sorted(p.value for p in denied))
        raise PluginError(
            PluginErrorCode.PERMISSION_DENIED,
            f"permissions denied: {names}",
        )
