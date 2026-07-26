"""Plugin framework configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PluginConfig:
    enabled: bool = True
    # Hot-load allowed in staging/dev only (still no remote install).
    hot_load: bool = True
    core_version: str = "0.9.0rc1"
    # Allowed import roots for entry_point modules (fail closed).
    allowed_entry_prefixes: tuple[str, ...] = ("cobra_core.plugins.samples.",)
    # Reserved plugin_id prefixes that third-party plugins may not use.
    reserved_namespaces: tuple[str, ...] = ("cobra.", "core.", "system.")
    plugins_root: str = ""  # empty → default samples dir

    def plugins_path(self) -> Path:
        if self.plugins_root:
            return Path(self.plugins_root)
        return Path(__file__).resolve().parent / "samples"


def load_plugin_config(env: dict[str, str] | None = None) -> PluginConfig:
    e = env if env is not None else os.environ
    prefixes = e.get("PEF_ALLOWED_ENTRY_PREFIXES", "cobra_core.plugins.samples.")
    reserved = e.get("PEF_RESERVED_NAMESPACES", "cobra.,core.,system.")
    return PluginConfig(
        enabled=_bool(e.get("PEF_ENABLED"), True),
        hot_load=_bool(e.get("PEF_HOT_LOAD"), True),
        core_version=(e.get("COBRA_CORE_VERSION") or "0.9.0rc1").strip(),
        allowed_entry_prefixes=tuple(
            p.strip() for p in prefixes.split(",") if p.strip()
        ),
        reserved_namespaces=tuple(p.strip() for p in reserved.split(",") if p.strip()),
        plugins_root=(e.get("PEF_PLUGINS_ROOT") or "").strip(),
    )
