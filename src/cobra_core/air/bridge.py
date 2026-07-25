"""Bridge AIR decisions into CIAL engine execution."""

from __future__ import annotations

from cobra_core.air.catalog import build_default_catalog
from cobra_core.air.policy import AirPolicyConfig, load_air_policy
from cobra_core.air.profiles import air_request_from_profile, get_air_profile
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.router import AdaptiveRouter
from cobra_core.air.types import AirDecision, AirRequest
from cobra_core.cial.config import CialConfig
from cobra_core.cial.health import HealthState
from cobra_core.cial.types import RouteDecision, RoutingPolicy


def catalog_for_config(config: CialConfig) -> DescriptorRegistry:
    """
    Build AIR catalog from CIAL config / live gate.

    OpenAI is registered only when the live gate is open so AIR cannot
    select a live vendor while disabled.
    """
    return build_default_catalog(
        mock_model_id=config.mock_model,
        openai_model_id=config.openai_model,
        openai_enabled=config.can_use_live_provider,
        openai_health=HealthState.HEALTHY if config.can_use_live_provider else HealthState.UNKNOWN,
    )


def air_request_for_config(
    config: CialConfig,
    *,
    extra_capabilities: frozenset | None = None,
) -> AirRequest:
    """Build AirRequest from the active CIAL profile (capability contract)."""
    profile = get_air_profile(config.active_profile)
    req = air_request_from_profile(
        profile.profile_id,
        extra_capabilities=extra_capabilities,
    )
    # Carry offline fallback + live requirement into router metadata.
    meta = dict(req.metadata)
    meta["requires_live"] = profile.requires_live
    meta["allow_offline_fallback"] = profile.allow_offline_fallback
    # When live gate is closed, never require live selection.
    if profile.requires_live and not config.can_use_live_provider:
        meta["requires_live"] = False
        meta["live_gate_closed"] = True
    return AirRequest(
        task=req.task,
        capabilities=req.capabilities,
        priority=req.priority,
        budget=req.budget,
        latency=req.latency,
        profile_id=req.profile_id,
        metadata=meta,
    )


def build_adaptive_router(
    config: CialConfig,
    *,
    policy: AirPolicyConfig | None = None,
    registry: DescriptorRegistry | None = None,
) -> AdaptiveRouter:
    """Construct AIR with catalog + policy for the current config."""
    return AdaptiveRouter(
        registry or catalog_for_config(config),
        policy=policy or load_air_policy(),
    )


def air_decision_to_route_decision(decision: AirDecision) -> RouteDecision:
    """Map AIR decision onto existing CIAL RouteDecision for engine compatibility."""
    return RouteDecision(
        provider_id=decision.provider_id,
        model_id=decision.model_id,
        policy=RoutingPolicy.DEFAULT,
        reason=decision.reason,
        health_state=decision.health_state,
        fallback_count=0,
    )
