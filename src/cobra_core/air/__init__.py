"""
Adaptive Intelligence Router (AIR) — KC-022.

Computer requests capabilities; AIR selects provider/model. Never part of
the Computer request contract: provider ids or model ids.
"""

from __future__ import annotations

from cobra_core.air.audit import AirAuditLog
from cobra_core.air.bridge import (
    air_decision_to_route_decision,
    air_request_for_config,
    build_adaptive_router,
    catalog_for_config,
)
from cobra_core.air.capabilities import (
    FUTURE_CAPABILITIES,
    INITIAL_CAPABILITIES,
    AirCapability,
    parse_air_capabilities,
)
from cobra_core.air.errors import AirRoutingError, AirRoutingFailureCode
from cobra_core.air.metrics import AirMetrics
from cobra_core.air.policy import AirPolicyConfig, load_air_policy
from cobra_core.air.profiles import (
    BUILTIN_AIR_PROFILE_IDS,
    AirProfilePolicy,
    air_request_from_contract,
    air_request_from_profile,
    get_air_profile,
)
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.router import AdaptiveRouter
from cobra_core.air.types import (
    AirDecision,
    AirRequest,
    BudgetClass,
    CostClass,
    LatencyClass,
    ModelDescriptor,
    PriorityClass,
    ProviderDescriptor,
)

__all__ = [
    "AirAuditLog",
    "AirCapability",
    "AirDecision",
    "AirMetrics",
    "AirPolicyConfig",
    "AirProfilePolicy",
    "AirRequest",
    "AirRoutingError",
    "AirRoutingFailureCode",
    "AdaptiveRouter",
    "BudgetClass",
    "BUILTIN_AIR_PROFILE_IDS",
    "CostClass",
    "DescriptorRegistry",
    "FUTURE_CAPABILITIES",
    "INITIAL_CAPABILITIES",
    "LatencyClass",
    "ModelDescriptor",
    "PriorityClass",
    "ProviderDescriptor",
    "air_decision_to_route_decision",
    "air_request_for_config",
    "air_request_from_contract",
    "air_request_from_profile",
    "build_adaptive_router",
    "catalog_for_config",
    "get_air_profile",
    "load_air_policy",
    "parse_air_capabilities",
]
