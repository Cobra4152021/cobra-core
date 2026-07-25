"""
Cobra Intelligence Abstraction Layer (CIAL).

Provider-neutral inference contracts inside Cobra Core. Protocol V1 remains
the external wire; Computer continues to talk only to Core.
"""

from __future__ import annotations

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.guards import LiveRequestGuard
from cobra_core.cial.health import HealthState
from cobra_core.cial.profiles import InferenceProfile, resolve_profile
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider
from cobra_core.cial.types import (
    GenerateRequest,
    InferenceResult,
    ModelRecord,
    RoutingPolicy,
    RoutingRequest,
)

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
