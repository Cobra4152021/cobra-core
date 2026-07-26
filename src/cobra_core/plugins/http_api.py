"""Authenticated Plugin Framework HTTP handlers (no upload / no remote install)."""

from __future__ import annotations

from typing import Any

from cobra_core.plugins.audit import PLUGIN_AUDIT
from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.manager import PLUGIN_MANAGER
from cobra_core.plugins.metrics import PLUGIN_METRICS


def handle_plugins_list() -> dict[str, Any]:
    return {"ok": True, "plugins": PLUGIN_MANAGER.list_plugins()}


def handle_plugins_status() -> dict[str, Any]:
    return PLUGIN_MANAGER.status()


def handle_plugin_get(plugin_id: str) -> tuple[int, dict[str, Any]]:
    try:
        return 200, {"ok": True, "plugin": PLUGIN_MANAGER.get(plugin_id)}
    except PluginError as exc:
        status = 404 if exc.code == PluginErrorCode.NOT_FOUND else 400
        return status, {
            "ok": False,
            "error": {"code": exc.code.value, "message": exc.message},
        }


def handle_plugin_enable(plugin_id: str, *, actor: str = "admin") -> tuple[int, dict[str, Any]]:
    try:
        PLUGIN_MANAGER.ensure_bootstrapped()
        rec = PLUGIN_MANAGER.enable(plugin_id, actor=actor)
        return 200, {"ok": True, "plugin": rec.public_dict()}
    except PluginError as exc:
        status = 404 if exc.code == PluginErrorCode.NOT_FOUND else 400
        return status, {
            "ok": False,
            "error": {"code": exc.code.value, "message": exc.message},
        }


def handle_plugin_disable(plugin_id: str, *, actor: str = "admin") -> tuple[int, dict[str, Any]]:
    try:
        PLUGIN_MANAGER.ensure_bootstrapped()
        rec = PLUGIN_MANAGER.disable(plugin_id, actor=actor)
        return 200, {"ok": True, "plugin": rec.public_dict()}
    except PluginError as exc:
        status = 404 if exc.code == PluginErrorCode.NOT_FOUND else 400
        return status, {
            "ok": False,
            "error": {"code": exc.code.value, "message": exc.message},
        }


def handle_plugins_metrics() -> dict[str, Any]:
    return {"ok": True, "metrics": PLUGIN_METRICS.snapshot()}


def handle_plugins_audit(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "entries": PLUGIN_AUDIT.recent(limit=limit)}
