"""Discover and import local plugin packages (no remote install / no codegen)."""

from __future__ import annotations

import importlib
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from cobra_core.plugins.audit import PLUGIN_AUDIT
from cobra_core.plugins.config import PluginConfig
from cobra_core.plugins.errors import PluginError, PluginErrorCode
from cobra_core.plugins.manifest import load_manifest_file
from cobra_core.plugins.metrics import PLUGIN_METRICS
from cobra_core.plugins.registry import PLUGIN_REGISTRY, PluginRegistry
from cobra_core.plugins.schemas import ExtensionRecord, PluginRecord, PluginState, PluginType
from cobra_core.plugins.validator import validate_manifest


class PluginExtension(Protocol):
    """Contract implemented by plugin entry modules."""

    def register(self) -> dict[str, Any] | list[dict[str, Any]]:
        """Return extension payload(s); must not mutate Core objects."""
        ...


def discover_manifests(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    found: list[Path] = []
    for child in sorted(root.iterdir()):
        if child.is_dir():
            manifest = child / "plugin.json"
            if manifest.is_file():
                found.append(manifest)
    return found


def _entry_file_for(entry_point: str) -> Path | None:
    """Resolve a Core-local module path without importing or executing plugin code."""
    parts = [part for part in entry_point.split(".") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        return None
    source_root = Path(__file__).resolve().parents[2]
    module_path = source_root.joinpath(*parts)
    py_file = module_path.with_suffix(".py")
    package_file = module_path / "__init__.py"
    candidate = py_file if py_file.is_file() else package_file
    try:
        candidate.resolve().relative_to(source_root.resolve())
    except (OSError, ValueError):
        return None
    return candidate if candidate.is_file() else None


def load_plugin_module(entry_point: str, config: PluginConfig) -> Any:
    if not any(entry_point.startswith(p) for p in config.allowed_entry_prefixes):
        raise PluginError(
            PluginErrorCode.VALIDATION_FAILED,
            f"entry_point not allowed: {entry_point}",
        )
    try:
        return importlib.import_module(entry_point)
    except Exception as exc:  # noqa: BLE001
        raise PluginError(
            PluginErrorCode.LOAD_FAILED, f"import failed: {type(exc).__name__}"
        ) from exc


def register_from_module(
    plugin_id: str,
    plugin_type: PluginType,
    module: Any,
    registry: PluginRegistry,
) -> list[ExtensionRecord]:
    register: Callable[[], Any] | None = getattr(module, "register", None)
    if register is None or not callable(register):
        raise PluginError(
            PluginErrorCode.LOAD_FAILED,
            "entry_point must expose register()",
        )
    result = register()
    payloads: list[dict[str, Any]]
    if isinstance(result, dict):
        payloads = [result]
    elif isinstance(result, list):
        payloads = [p for p in result if isinstance(p, dict)]
    else:
        raise PluginError(PluginErrorCode.LOAD_FAILED, "register() must return dict or list")
    records: list[ExtensionRecord] = []
    for i, payload in enumerate(payloads):
        ext_id = str(payload.get("extension_id") or f"{plugin_id}:{i}")
        # Strip anything that looks like a Core mutation hook.
        safe = {
            k: v
            for k, v in payload.items()
            if k not in {"mutate_core", "patch_core", "monkeypatch"}
        }
        rec = ExtensionRecord(
            plugin_id=plugin_id,
            plugin_type=plugin_type,
            extension_id=ext_id,
            payload=safe,
        )
        registry.register_extension(rec)
        records.append(rec)
    return records


class PluginLoader:
    def __init__(
        self,
        *,
        config: PluginConfig,
        registry: PluginRegistry | None = None,
    ) -> None:
        self.config = config
        self.registry = registry if registry is not None else PLUGIN_REGISTRY

    def discover(self) -> list[dict[str, Any]]:
        manifests = discover_manifests(self.config.plugins_path())
        out: list[dict[str, Any]] = []
        for path in manifests:
            try:
                m = load_manifest_file(path)
                rec = PluginRecord(
                    plugin_id=m["plugin_id"],
                    state=PluginState.DISCOVERED,
                    manifest=m,
                    path=str(path.parent),
                )
                self.registry.put(rec)
                out.append(rec.public_dict())
            except PluginError as exc:
                PLUGIN_METRICS.record_validation_error()
                PLUGIN_AUDIT.record(
                    "plugin_validation_failure",
                    path=str(path),
                    code=exc.code.value,
                    message=exc.message,
                )
        return out

    def validate(self, plugin_id: str) -> PluginRecord:
        rec = self.registry.get(plugin_id)
        path = Path(rec.path) / "plugin.json" if rec.path else None
        entry_file = None
        try:
            # Temporarily exclude self from duplicate check
            others = self.registry.ids() - {plugin_id}
            entry_file = _entry_file_for(str(rec.manifest.get("entry_point") or ""))
            validate_manifest(
                rec.manifest,
                config=self.config,
                manifest_path=path if path and path.is_file() else None,
                entry_file=entry_file if entry_file and entry_file.is_file() else None,
                known_ids=others,
            )
            # Dependencies must already be loaded/enabled if declared.
            for dep in rec.manifest.get("dependencies") or []:
                if dep not in self.registry.ids():
                    raise PluginError(
                        PluginErrorCode.DEPENDENCY_MISSING,
                        f"missing dependency: {dep}",
                    )
            return self.registry.set_state(plugin_id, PluginState.VALIDATED)
        except PluginError as exc:
            PLUGIN_METRICS.record_validation_error()
            if exc.code == PluginErrorCode.COMPATIBILITY_FAILED:
                PLUGIN_AUDIT.record(
                    "plugin_compatibility_failure",
                    plugin_id=plugin_id,
                    message=exc.message,
                )
            elif exc.code == PluginErrorCode.PERMISSION_DENIED:
                PLUGIN_AUDIT.record(
                    "permission_denial",
                    plugin_id=plugin_id,
                    message=exc.message,
                )
            else:
                PLUGIN_AUDIT.record(
                    "plugin_validation_failure",
                    plugin_id=plugin_id,
                    code=exc.code.value,
                    message=exc.message,
                )
            self.registry.set_state(plugin_id, PluginState.FAILED, error=exc.message)
            raise

    def load(self, plugin_id: str) -> PluginRecord:
        t0 = time.perf_counter()
        try:
            rec = self.validate(plugin_id)
            module = load_plugin_module(str(rec.manifest["entry_point"]), self.config)
            ptype = PluginType(rec.manifest["plugin_type"])
            register_from_module(plugin_id, ptype, module, self.registry)
            ms = (time.perf_counter() - t0) * 1000
            PLUGIN_METRICS.record_loaded(latency_ms=ms)
            with_time = self.registry.get(plugin_id)
            with_time.loaded_at = time.time()
            with_time.state = PluginState.LOADED
            with_time.error = ""
            self.registry.put(with_time)
            PLUGIN_AUDIT.record("plugin_loaded", plugin_id=plugin_id, latency_ms=round(ms, 2))
            return with_time
        except PluginError:
            PLUGIN_METRICS.record_failure()
            raise
        except Exception as exc:  # noqa: BLE001
            PLUGIN_METRICS.record_failure()
            self.registry.set_state(plugin_id, PluginState.FAILED, error=type(exc).__name__)
            raise PluginError(PluginErrorCode.LOAD_FAILED, type(exc).__name__) from exc
