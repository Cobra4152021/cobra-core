"""Plugin types, states, and public snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PluginType(StrEnum):
    ISF_SKILL = "isf_skill"
    KEF_CONNECTOR = "kef_connector"
    WORKFLOW_TEMPLATE = "workflow_template"
    CASE_TEMPLATE = "case_template"
    BENCHMARK_DATASET = "benchmark_dataset"
    REPORT = "report"
    VALIDATOR = "validator"
    POLICY = "policy"


class PluginState(StrEnum):
    DISCOVERED = "discovered"
    VALIDATED = "validated"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    FAILED = "failed"


class Permission(StrEnum):
    REGISTER_SKILL = "register_skill"
    REGISTER_CONNECTOR = "register_connector"
    REGISTER_WORKFLOW = "register_workflow"
    REGISTER_REPORT = "register_report"
    REGISTER_DATASET = "register_dataset"
    REGISTER_CASE_TEMPLATE = "register_case_template"
    REGISTER_VALIDATOR = "register_validator"
    REGISTER_POLICY = "register_policy"


# Type → required permission mapping (fail closed if missing).
TYPE_PERMISSIONS: dict[PluginType, Permission] = {
    PluginType.ISF_SKILL: Permission.REGISTER_SKILL,
    PluginType.KEF_CONNECTOR: Permission.REGISTER_CONNECTOR,
    PluginType.WORKFLOW_TEMPLATE: Permission.REGISTER_WORKFLOW,
    PluginType.CASE_TEMPLATE: Permission.REGISTER_CASE_TEMPLATE,
    PluginType.BENCHMARK_DATASET: Permission.REGISTER_DATASET,
    PluginType.REPORT: Permission.REGISTER_REPORT,
    PluginType.VALIDATOR: Permission.REGISTER_VALIDATOR,
    PluginType.POLICY: Permission.REGISTER_POLICY,
}


@dataclass(frozen=True)
class ExtensionRecord:
    """Opaque extension payload registered by a plugin (never mutates Core)."""

    plugin_id: str
    plugin_type: PluginType
    extension_id: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginRecord:
    plugin_id: str
    state: PluginState
    manifest: dict[str, Any]
    path: str = ""
    error: str = ""
    loaded_at: float | None = None
    enabled_at: float | None = None
    extensions: list[ExtensionRecord] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        m = self.manifest
        return {
            "plugin_id": self.plugin_id,
            "name": m.get("name"),
            "version": m.get("version"),
            "author": m.get("author"),
            "description": m.get("description"),
            "plugin_type": m.get("plugin_type"),
            "state": self.state.value,
            "error": self.error or None,
            "required_permissions": list(m.get("required_permissions") or []),
            "supported_core_version": m.get("supported_core_version"),
            "extension_count": len(self.extensions),
            "loaded_at": self.loaded_at,
            "enabled_at": self.enabled_at,
        }
