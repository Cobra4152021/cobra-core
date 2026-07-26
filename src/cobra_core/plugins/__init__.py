"""
KC-033 — Plugin & Extension Framework (PEF).

Declarative, versioned, permission-controlled extensions.
No remote downloads. No runtime code generation.
"""

from cobra_core.plugins.config import PluginConfig, load_plugin_config
from cobra_core.plugins.manager import PLUGIN_MANAGER, PluginManager

__all__ = [
    "PLUGIN_MANAGER",
    "PluginConfig",
    "PluginManager",
    "load_plugin_config",
]
