"""In-memory plugin + extension registry (does not mutate Core objects)."""

from __future__ import annotations

import threading
from typing import Any

from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.schemas import ExtensionRecord, PluginRecord, PluginState, PluginType


class PluginRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._plugins: dict[str, PluginRecord] = {}
        self._extensions: dict[str, list[ExtensionRecord]] = {}

    def clear(self) -> None:
        with self._lock:
            self._plugins.clear()
            self._extensions.clear()

    def put(self, record: PluginRecord) -> None:
        with self._lock:
            self._plugins[record.plugin_id] = record

    def get(self, plugin_id: str) -> PluginRecord:
        with self._lock:
            try:
                return self._plugins[plugin_id]
            except KeyError as exc:
                raise PluginError(
                    PluginErrorCode.NOT_FOUND, f"plugin not found: {plugin_id}"
                ) from exc

    def remove(self, plugin_id: str) -> None:
        with self._lock:
            self._plugins.pop(plugin_id, None)
            self._extensions.pop(plugin_id, None)

    def list_plugins(self) -> list[PluginRecord]:
        with self._lock:
            return [self._plugins[k] for k in sorted(self._plugins)]

    def ids(self) -> set[str]:
        with self._lock:
            return set(self._plugins)

    def set_state(self, plugin_id: str, state: PluginState, *, error: str = "") -> PluginRecord:
        with self._lock:
            rec = self._plugins[plugin_id]
            rec.state = state
            rec.error = error
            return rec

    def register_extension(self, ext: ExtensionRecord) -> None:
        with self._lock:
            bucket = self._extensions.setdefault(ext.plugin_id, [])
            # Replace same extension_id
            bucket[:] = [e for e in bucket if e.extension_id != ext.extension_id]
            bucket.append(ext)
            if ext.plugin_id in self._plugins:
                self._plugins[ext.plugin_id].extensions = list(bucket)

    def extensions_for(self, plugin_id: str) -> list[ExtensionRecord]:
        with self._lock:
            return list(self._extensions.get(plugin_id, []))

    def extensions_by_type(self, plugin_type: PluginType) -> list[ExtensionRecord]:
        with self._lock:
            out: list[ExtensionRecord] = []
            for items in self._extensions.values():
                out.extend(e for e in items if e.plugin_type == plugin_type)
            return out

    def status_snapshot(self) -> dict[str, Any]:
        with self._lock:
            by_state: dict[str, int] = {}
            for rec in self._plugins.values():
                by_state[rec.state.value] = by_state.get(rec.state.value, 0) + 1
            return {
                "total": len(self._plugins),
                "by_state": by_state,
                "extension_total": sum(len(v) for v in self._extensions.values()),
            }


PLUGIN_REGISTRY = PluginRegistry()
