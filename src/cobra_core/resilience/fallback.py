"""Constrained fallback (never silent capability downgrade)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from cobra_core.air.capabilities import AirCapability
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.cial.health import HealthState
from cobra_core.resilience.config import ResilienceConfig
from cobra_core.resilience.errors import FailureCategory, traits_for
from cobra_core.resilience.types import RouteTarget


@dataclass(frozen=True)
class FallbackDecision:
    allowed: bool
    reason: str
    target: RouteTarget | None = None
    capability_equivalence: str = ""


def evaluate_fallback(
    *,
    cfg: ResilienceConfig,
    failure: FailureCategory,
    required: frozenset[AirCapability],
    primary: RouteTarget,
    catalog: DescriptorRegistry,
    allow_offline_fallback: bool,
    live_gate_open: bool,
    circuit_allows: Callable[[str, str], bool] | None = None,
) -> FallbackDecision:
    """
    Select an alternative that satisfies every required capability.

    Vision → mock is never allowed (mock lacks vision).
    Live → mock only when offline fallback explicitly permitted.
    """
    if not cfg.allow_fallback:
        return FallbackDecision(False, "fallback_disabled_by_config")
    if not traits_for(failure).fallback_eligible:
        return FallbackDecision(False, f"failure_not_fallback_eligible:{failure.value}")

    if AirCapability.VISION in required and primary.provider_id == "openai":
        # Hard rule: never downgrade vision to text-only mock.
        return FallbackDecision(
            False,
            "vision_downgrade_forbidden",
            capability_equivalence="fail",
        )

    candidates: list[tuple[str, str]] = []
    if allow_offline_fallback and primary.provider_id != "mock":
        for p in catalog.list_providers():
            if p.provider_id != "mock" or not p.enabled:
                continue
            for m in p.models:
                if m.enabled:
                    candidates.append((p.provider_id, m.model_id))
    if live_gate_open and primary.provider_id == "mock":
        for p in catalog.list_providers():
            if p.provider_id != "openai" or not p.enabled:
                continue
            for m in p.models:
                if m.enabled and (not m.requires_live or live_gate_open):
                    candidates.append((p.provider_id, m.model_id))

    saw_capability_fail = False
    for provider_id, model_id in candidates:
        if provider_id == primary.provider_id and model_id == primary.model_id:
            continue
        try:
            model = catalog.get_model(provider_id, model_id)
        except Exception:  # noqa: BLE001
            continue
        if model is None or not model.enabled:
            continue
        if model.requires_live and not live_gate_open:
            continue
        if not required.issubset(model.capabilities):
            saw_capability_fail = True
            continue
        if AirCapability.STRUCTURED_OUTPUT in required and (
            AirCapability.STRUCTURED_OUTPUT not in model.capabilities
        ):
            saw_capability_fail = True
            continue
        if model.health in {HealthState.UNAVAILABLE, HealthState.DISABLED}:
            continue
        if circuit_allows is not None and not circuit_allows(provider_id, model_id):
            continue
        if provider_id == "mock" and not allow_offline_fallback:
            continue
        return FallbackDecision(
            True,
            "fallback_selected",
            target=RouteTarget(
                provider_id=provider_id,
                model_id=model_id,
                route_reason=f"rrf_fallback_from_{primary.provider_id}",
                capabilities=frozenset(model.capabilities),
            ),
            capability_equivalence="pass",
        )

    if saw_capability_fail:
        return FallbackDecision(
            False,
            "capability_equivalence_failed",
            capability_equivalence="fail",
        )
    return FallbackDecision(False, "no_eligible_fallback", capability_equivalence="fail")
