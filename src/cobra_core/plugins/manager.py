"""Plugin manager — lifecycle orchestration."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.plugins.audit import PLUGIN_AUDIT
from cobra_core.plugins.config import PluginConfig, load_plugin_config
from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.loader import PluginLoader
from cobra_core.plugins.metrics import PLUGIN_METRICS
from cobra_core.plugins.registry import PLUGIN_REGISTRY, PluginRegistry
from cobra_core.plugins.schemas import PluginRecord, PluginState


class PluginManager:
    def __init__(
        self,
        *,
        config: PluginConfig | None = None,
        registry: PluginRegistry | None = None,
    ) -> None:
        self.config = config or load_plugin_config()
        self.registry = registry if registry is not None else PLUGIN_REGISTRY
        self.loader = PluginLoader(config=self.config, registry=self.registry)
        self._bootstrapped = False

    def bootstrap_samples(self) -> list[str]:
        """Discover + load + enable reference sample plugins (staging/dev)."""
        if not self.config.enabled:
            self._bootstrapped = True
            return []
        self.loader.discover()
        enabled: list[str] = []
        for rec in list(self.registry.list_plugins()):
            try:
                self.load(rec.plugin_id)
                self.enable(rec.plugin_id, actor="bootstrap")
                enabled.append(rec.plugin_id)
            except PluginError:
                continue
        self._bootstrapped = True
        return enabled

    def ensure_bootstrapped(self) -> None:
        """Idempotent sample discovery for API surfaces (local packages only)."""
        if self._bootstrapped or not self.config.enabled:
            return
        self.bootstrap_samples()

    def discover(self) -> list[dict[str, Any]]:
        return self.loader.discover()

    def load(self, plugin_id: str) -> PluginRecord:
        if not self.config.enabled:
            raise PluginError(PluginErrorCode.STATE_INVALID, "PEF disabled")
        return self.loader.load(plugin_id)

    def enable(self, plugin_id: str, *, actor: str = "admin") -> PluginRecord:
        rec = self.registry.get(plugin_id)
        if rec.state not in {PluginState.LOADED, PluginState.DISABLED, PluginState.ENABLED}:
            if rec.state == PluginState.DISCOVERED or rec.state == PluginState.VALIDATED:
                rec = self.load(plugin_id)
            else:
                raise PluginError(
                    PluginErrorCode.STATE_INVALID,
                    f"cannot enable from state {rec.state.value}",
                )
        if rec.state == PluginState.ENABLED:
            return rec
        rec.state = PluginState.ENABLED
        rec.enabled_at = time.time()
        rec.error = ""
        self.registry.put(rec)
        PLUGIN_METRICS.record_enabled(enabled=True)
        PLUGIN_AUDIT.record("plugin_enabled", actor=actor, plugin_id=plugin_id)
        return rec

    def disable(self, plugin_id: str, *, actor: str = "admin") -> PluginRecord:
        rec = self.registry.get(plugin_id)
        if rec.state == PluginState.DISABLED:
            return rec
        if rec.state not in {PluginState.ENABLED, PluginState.LOADED}:
            raise PluginError(
                PluginErrorCode.STATE_INVALID,
                f"cannot disable from state {rec.state.value}",
            )
        was_enabled = rec.state == PluginState.ENABLED
        rec.state = PluginState.DISABLED
        rec.enabled_at = None
        self.registry.put(rec)
        if was_enabled:
            PLUGIN_METRICS.record_enabled(enabled=False)
        PLUGIN_AUDIT.record("plugin_disabled", actor=actor, plugin_id=plugin_id)
        return rec

    def unload(self, plugin_id: str, *, actor: str = "admin") -> None:
        rec = self.registry.get(plugin_id)
        if rec.state == PluginState.ENABLED:
            self.disable(plugin_id, actor=actor)
        self.registry.remove(plugin_id)
        PLUGIN_AUDIT.record("plugin_unloaded", actor=actor, plugin_id=plugin_id)

    def reload(self, plugin_id: str, *, actor: str = "admin") -> PluginRecord:
        if not self.config.hot_load:
            raise PluginError(PluginErrorCode.STATE_INVALID, "hot-load disabled")
        path = self.registry.get(plugin_id).path
        was_enabled = self.registry.get(plugin_id).state == PluginState.ENABLED
        self.unload(plugin_id, actor=actor)
        # Re-discover that path
        from pathlib import Path

        from cobra_core.plugins.manifest import load_manifest_file
        from cobra_core.plugins.schemas import PluginRecord as PR

        manifest_path = Path(path) / "plugin.json"
        m = load_manifest_file(manifest_path)
        self.registry.put(
            PR(
                plugin_id=m["plugin_id"],
                state=PluginState.DISCOVERED,
                manifest=m,
                path=path,
            )
        )
        rec = self.load(plugin_id)
        if was_enabled:
            rec = self.enable(plugin_id, actor=actor)
        PLUGIN_AUDIT.record("plugin_reloaded", actor=actor, plugin_id=plugin_id)
        return rec

    def get(self, plugin_id: str) -> dict[str, Any]:
        self.ensure_bootstrapped()
        return self.registry.get(plugin_id).public_dict()

    def list_plugins(self) -> list[dict[str, Any]]:
        self.ensure_bootstrapped()
        return [r.public_dict() for r in self.registry.list_plugins()]

    def status(self) -> dict[str, Any]:
        self.ensure_bootstrapped()
        return {
            "ok": True,
            "enabled": self.config.enabled,
            "hot_load": self.config.hot_load,
            "core_version": self.config.core_version,
            "plugins_root": str(self.config.plugins_path()),
            "registry": self.registry.status_snapshot(),
            "metrics": PLUGIN_METRICS.snapshot(),
        }

    def reset_for_tests(self) -> None:
        self.registry.clear()
        PLUGIN_METRICS.clear()
        PLUGIN_AUDIT.clear()
        self._bootstrapped = False
        self.config = load_plugin_config()
        self.loader = PluginLoader(config=self.config, registry=self.registry)


PLUGIN_MANAGER = PluginManager()
