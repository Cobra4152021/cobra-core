"""Deterministic CIAL routing (no automatic fallback execution in Phase 1)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState, is_routable_health
from cobra_core.cial.registry import ModelRegistry
from cobra_core.cial.types import (
    ModelRecord,
    RouteDecision,
    RoutingPolicy,
    RoutingRequest,
    latency_rank,
    quality_rank,
)


def _estimated_cost(model: ModelRecord) -> float:
    """Sort key for lowest_cost; unknown costs sort after known costs."""
    inp = model.estimated_input_cost
    out = model.estimated_output_cost
    if inp is None and out is None:
        return float("inf")
    return float(inp or 0.0) + float(out or 0.0)


def _health_preference(state: HealthState) -> int:
    """Lower is better: healthy before unknown before degraded."""
    return {
        HealthState.HEALTHY: 0,
        HealthState.UNKNOWN: 1,
        HealthState.DEGRADED: 2,
    }.get(state, 99)


def eligible_models(
    registry: ModelRegistry,
    *,
    required_capabilities: frozenset[Capability] = frozenset(),
) -> list[ModelRecord]:
    """Models that are enabled, routable by health, and capability-matched."""
    out: list[ModelRecord] = []
    for model in registry.list_models():
        if not model.enabled:
            continue
        if not is_routable_health(model.health):
            continue
        if required_capabilities and not model.has_capabilities(required_capabilities):
            continue
        out.append(model)
    return out


class DeterministicRouter:
    """
    Select exactly one model for a RoutingRequest.

    Tie-breakers (always applied after policy score): health preference,
    then (provider_id, model_id) lexicographic ascending.
    """

    def __init__(self, registry: ModelRegistry) -> None:
        self.registry = registry

    def route(self, request: RoutingRequest) -> RouteDecision:
        if request.policy == RoutingPolicy.MANUAL:
            return self._route_manual(request)

        required = set(request.required_capabilities)
        if request.policy == RoutingPolicy.REASONING:
            required.add(Capability.REASONING)
        elif request.policy == RoutingPolicy.RESEARCH:
            required.add(Capability.RESEARCH)
        required_fs = frozenset(required)

        candidates = eligible_models(self.registry, required_capabilities=required_fs)
        if not candidates:
            raise CialError(
                CialErrorCode.ROUTING_FAILED,
                "no eligible model for routing policy",
            )

        if request.policy == RoutingPolicy.DEFAULT:
            chosen = self._pick_default(candidates, request.preferred_model_id)
            reason = "default_policy"
        elif request.policy == RoutingPolicy.LOWEST_COST:
            chosen = self._pick_by_key(candidates, key=lambda m: (_estimated_cost(m),))
            reason = "lowest_cost"
        elif request.policy == RoutingPolicy.LOWEST_LATENCY:
            chosen = self._pick_by_key(
                candidates, key=lambda m: (latency_rank(m.latency_tier),)
            )
            reason = "lowest_latency"
        elif request.policy == RoutingPolicy.HIGHEST_QUALITY:
            chosen = self._pick_by_key(
                candidates,
                key=lambda m: (-quality_rank(m.quality_tier),),
            )
            reason = "highest_quality"
        elif request.policy == RoutingPolicy.REASONING:
            chosen = self._pick_by_key(
                candidates,
                key=lambda m: (-quality_rank(m.quality_tier),),
            )
            reason = "reasoning_capability"
        elif request.policy == RoutingPolicy.RESEARCH:
            chosen = self._pick_by_key(
                candidates,
                key=lambda m: (-quality_rank(m.quality_tier),),
            )
            reason = "research_capability"
        else:
            raise CialError(
                CialErrorCode.ROUTING_FAILED,
                f"unsupported routing policy: {request.policy.value}",
            )

        return RouteDecision(
            provider_id=chosen.provider_id,
            model_id=chosen.model_id,
            policy=request.policy,
            reason=reason,
            health_state=chosen.health,
            fallback_count=0,
        )

    def _route_manual(self, request: RoutingRequest) -> RouteDecision:
        if not request.manual_provider_id or not request.manual_model_id:
            raise CialError(
                CialErrorCode.ROUTING_FAILED,
                "manual routing requires provider_id and model_id",
            )
        try:
            model = self.registry.get(request.manual_provider_id, request.manual_model_id)
        except CialError:
            raise CialError(
                CialErrorCode.MODEL_NOT_FOUND,
                "manual model not found or not registered",
            ) from None

        if not model.enabled:
            raise CialError(CialErrorCode.MODEL_DISABLED, "manual model is disabled")
        if model.health == HealthState.DISABLED:
            raise CialError(CialErrorCode.MODEL_DISABLED, "manual model health is disabled")
        if model.health == HealthState.UNAVAILABLE:
            raise CialError(
                CialErrorCode.PROVIDER_UNAVAILABLE,
                "manual model is unavailable",
            )
        if request.required_capabilities and not model.has_capabilities(
            request.required_capabilities
        ):
            raise CialError(
                CialErrorCode.CAPABILITY_MISMATCH,
                "manual model lacks required capabilities",
            )

        return RouteDecision(
            provider_id=model.provider_id,
            model_id=model.model_id,
            policy=RoutingPolicy.MANUAL,
            reason="manual_selection",
            health_state=model.health,
            fallback_count=0,
        )

    def _pick_default(
        self, candidates: list[ModelRecord], preferred_model_id: str | None
    ) -> ModelRecord:
        if preferred_model_id:
            preferred = [m for m in candidates if m.model_id == preferred_model_id]
            if preferred:
                return self._pick_by_key(preferred, key=lambda _m: (0,))
        return self._pick_by_key(candidates, key=lambda _m: (0,))

    def _pick_by_key(
        self,
        candidates: list[ModelRecord],
        *,
        key: Callable[[ModelRecord], tuple[Any, ...]],
    ) -> ModelRecord:
        def sort_key(m: ModelRecord) -> tuple[Any, ...]:
            return (
                *key(m),
                _health_preference(m.health),
                m.provider_id,
                m.model_id,
            )

        return sorted(candidates, key=sort_key)[0]
