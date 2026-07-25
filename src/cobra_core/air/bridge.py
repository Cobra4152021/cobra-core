"""Bridge AIR decisions into CIAL engine execution."""

from __future__ import annotations

from typing import Any

from cobra_core.air.audit import AIR_AUDIT
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.catalog import build_default_catalog
from cobra_core.air.metrics import AIR_METRICS
from cobra_core.air.policy import AirPolicyConfig, load_air_policy
from cobra_core.air.profiles import air_request_from_profile, get_air_profile
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.router import AdaptiveRouter
from cobra_core.air.types import AirDecision, AirRequest, BudgetClass, LatencyClass, PriorityClass
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
    extra_capabilities: frozenset[AirCapability] | None = None,
    capabilities_override: frozenset[AirCapability] | None = None,
    correlation_id: str = "",
    priority: PriorityClass | None = None,
    budget: BudgetClass | None = None,
    latency: LatencyClass | None = None,
    task: str | None = None,
) -> AirRequest:
    """Build AirRequest from the active CIAL profile (capability contract)."""
    profile = get_air_profile(config.active_profile)
    if capabilities_override is not None:
        caps = capabilities_override
        req_task = task or "capability_request"
        req_priority = priority or PriorityClass.NORMAL
        req_budget = budget or BudgetClass.NORMAL
        req_latency = latency or LatencyClass.NORMAL
        meta: dict[str, Any] = {
            "requires_live": bool(profile.requires_live and config.can_use_live_provider),
            "allow_offline_fallback": profile.allow_offline_fallback,
        }
        if profile.requires_live and not config.can_use_live_provider:
            meta["requires_live"] = False
            meta["live_gate_closed"] = True
        return AirRequest(
            task=req_task,
            capabilities=caps,
            priority=req_priority,
            budget=req_budget,
            latency=req_latency,
            profile_id=profile.profile_id,
            correlation_id=correlation_id or "",
            metadata=meta,
        )

    req = air_request_from_profile(
        profile.profile_id,
        extra_capabilities=extra_capabilities,
        priority=priority,
        budget=budget,
        latency=latency,
        task=task,
    )
    meta = dict(req.metadata)
    meta["requires_live"] = profile.requires_live
    meta["allow_offline_fallback"] = profile.allow_offline_fallback
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
        correlation_id=correlation_id or "",
        metadata=meta,
    )


def build_adaptive_router(
    config: CialConfig,
    *,
    policy: AirPolicyConfig | None = None,
    registry: DescriptorRegistry | None = None,
) -> AdaptiveRouter:
    """Construct AIR with catalog + shared process audit/metrics."""
    return AdaptiveRouter(
        registry or catalog_for_config(config),
        policy=policy or load_air_policy(),
        audit=AIR_AUDIT,
        metrics=AIR_METRICS,
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


def safe_catalog_snapshot(config: CialConfig) -> dict[str, Any]:
    """Safe runtime catalog view (no secrets)."""
    reg = catalog_for_config(config)
    providers = []
    for p in reg.list_providers():
        providers.append(
            {
                "provider_id": p.provider_id,
                "enabled": p.enabled,
                "models": [
                    {
                        "model_id": m.model_id,
                        "capabilities": sorted(c.value for c in m.capabilities),
                        "estimated_cost": m.estimated_cost.value,
                        "latency": m.latency.value,
                        "health": m.health.value,
                        "requires_live": m.requires_live,
                    }
                    for m in p.models
                ],
            }
        )
    return {
        "air_enabled": True,
        "live_gate_open": config.can_use_live_provider,
        "active_profile": config.active_profile,
        "providers": providers,
    }
