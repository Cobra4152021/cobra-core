"""
Cobra Intelligence Abstraction Layer (CIAL).

Provider-neutral inference contracts inside Cobra Core. Protocol V1 remains
the external wire; Computer continues to talk only to Core.

Heavy imports (engine → AIR) are lazy to avoid circular import with ``air``.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "Capability",
    "CialConfig",
    "CialEngine",
    "CialError",
    "CialErrorCode",
    "GenerateRequest",
    "HealthState",
    "InferenceProfile",
    "InferenceResult",
    "LiveRequestGuard",
    "MockProvider",
    "ModelRecord",
    "OpenAICompatibleProvider",
    "RoutingPolicy",
    "RoutingRequest",
    "load_cial_config",
    "resolve_profile",
]


def __getattr__(name: str) -> Any:
    if name == "Capability":
        from cobra_core.cial.capabilities import Capability

        return Capability
    if name == "CialConfig":
        from cobra_core.cial.config import CialConfig

        return CialConfig
    if name == "load_cial_config":
        from cobra_core.cial.config import load_cial_config

        return load_cial_config
    if name == "CialEngine":
        from cobra_core.cial.engine import CialEngine

        return CialEngine
    if name in {"CialError", "CialErrorCode"}:
        from cobra_core.cial import errors as _errors

        return getattr(_errors, name)
    if name == "HealthState":
        from cobra_core.cial.health import HealthState

        return HealthState
    if name in {"InferenceProfile", "resolve_profile"}:
        from cobra_core.cial import profiles as _profiles

        return getattr(_profiles, name)
    if name == "LiveRequestGuard":
        from cobra_core.cial.guards import LiveRequestGuard

        return LiveRequestGuard
    if name == "MockProvider":
        from cobra_core.cial.providers.mock import MockProvider

        return MockProvider
    if name == "OpenAICompatibleProvider":
        from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider

        return OpenAICompatibleProvider
    if name in {
        "GenerateRequest",
        "InferenceResult",
        "ModelRecord",
        "RoutingPolicy",
        "RoutingRequest",
    }:
        from cobra_core.cial import types as _types

        return getattr(_types, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
