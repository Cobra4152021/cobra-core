"""CIAL deterministic routing unit tests (KC-019 Phase 1)."""

from __future__ import annotations

import pytest

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState
from cobra_core.cial.registry import ModelRegistry
from cobra_core.cial.router import DeterministicRouter, eligible_models
from cobra_core.cial.types import (
    LatencyTier,
    ModelRecord,
    QualityTier,
    RoutingPolicy,
    RoutingRequest,
)


def _model(
    model_id: str,
    *,
    provider_id: str = "mock",
    enabled: bool = True,
    health: HealthState = HealthState.HEALTHY,
    caps: frozenset[Capability] | None = None,
    quality: QualityTier = QualityTier.STANDARD,
    latency: LatencyTier = LatencyTier.STANDARD,
    in_cost: float | None = 1.0,
    out_cost: float | None = 1.0,
) -> ModelRecord:
    return ModelRecord(
        provider_id=provider_id,
        model_id=model_id,
        display_name=model_id,
        enabled=enabled,
        capabilities=caps or frozenset({Capability.TEXT}),
        context_window=8192,
        max_output_tokens=2048,
        supports_json=Capability.JSON in (caps or frozenset()),
        supports_tools=False,
        supports_vision=False,
        supports_streaming=False,
        quality_tier=quality,
        latency_tier=latency,
        estimated_input_cost=in_cost,
        estimated_output_cost=out_cost,
        revision="test",
        health=health,
    )


def _registry(*models: ModelRecord) -> ModelRegistry:
    reg = ModelRegistry()
    for m in models:
        reg.register(m)
    return reg


def test_disabled_model_exclusion() -> None:
    reg = _registry(
        _model("on", enabled=True),
        _model("off", enabled=False),
    )
    ids = {m.model_id for m in eligible_models(reg)}
    assert ids == {"on"}


def test_unhealthy_model_exclusion() -> None:
    reg = _registry(
        _model("ok", health=HealthState.HEALTHY),
        _model("down", health=HealthState.UNAVAILABLE),
        _model("off", health=HealthState.DISABLED),
        _model("deg", health=HealthState.DEGRADED),
    )
    ids = {m.model_id for m in eligible_models(reg)}
    assert ids == {"ok", "deg"}


def test_capability_matching() -> None:
    reg = _registry(
        _model("text-only", caps=frozenset({Capability.TEXT})),
        _model(
            "vision",
            caps=frozenset({Capability.TEXT, Capability.VISION}),
        ),
    )
    ids = {
        m.model_id
        for m in eligible_models(reg, required_capabilities=frozenset({Capability.VISION}))
    }
    assert ids == {"vision"}


def test_default_routing_prefers_configured_model() -> None:
    reg = _registry(_model("other"), _model("cobra-core-qwen3-8b"))
    decision = DeterministicRouter(reg).route(
        RoutingRequest(
            policy=RoutingPolicy.DEFAULT,
            preferred_model_id="cobra-core-qwen3-8b",
        )
    )
    assert decision.model_id == "cobra-core-qwen3-8b"
    assert decision.reason == "default_policy"


def test_lowest_cost_routing() -> None:
    reg = _registry(
        _model("expensive", in_cost=10.0, out_cost=10.0),
        _model("cheap", in_cost=0.1, out_cost=0.1),
    )
    decision = DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.LOWEST_COST))
    assert decision.model_id == "cheap"


def test_lowest_latency_routing() -> None:
    reg = _registry(
        _model("slow", latency=LatencyTier.SLOW),
        _model("fast", latency=LatencyTier.FAST),
    )
    decision = DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.LOWEST_LATENCY))
    assert decision.model_id == "fast"


def test_highest_quality_routing() -> None:
    reg = _registry(
        _model("basic", quality=QualityTier.LOW),
        _model("best", quality=QualityTier.PREMIUM),
    )
    decision = DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.HIGHEST_QUALITY))
    assert decision.model_id == "best"


def test_reasoning_and_research_policies() -> None:
    reg = _registry(
        _model("plain", caps=frozenset({Capability.TEXT})),
        _model(
            "reasoner",
            caps=frozenset({Capability.TEXT, Capability.REASONING}),
            quality=QualityTier.HIGH,
        ),
        _model(
            "researcher",
            caps=frozenset({Capability.TEXT, Capability.RESEARCH}),
            quality=QualityTier.PREMIUM,
        ),
    )
    r = DeterministicRouter(reg)
    assert r.route(RoutingRequest(policy=RoutingPolicy.REASONING)).model_id == "reasoner"
    assert r.route(RoutingRequest(policy=RoutingPolicy.RESEARCH)).model_id == "researcher"


def test_manual_routing() -> None:
    reg = _registry(_model("a"), _model("b"))
    decision = DeterministicRouter(reg).route(
        RoutingRequest(
            policy=RoutingPolicy.MANUAL,
            manual_provider_id="mock",
            manual_model_id="b",
        )
    )
    assert decision.model_id == "b"
    assert decision.reason == "manual_selection"


def test_invalid_manual_model() -> None:
    reg = _registry(_model("a"))
    with pytest.raises(CialError) as exc:
        DeterministicRouter(reg).route(
            RoutingRequest(
                policy=RoutingPolicy.MANUAL,
                manual_provider_id="mock",
                manual_model_id="missing",
            )
        )
    assert exc.value.code == CialErrorCode.MODEL_NOT_FOUND


def test_manual_disabled_and_unavailable() -> None:
    reg = _registry(
        _model("off", enabled=False),
        _model("down", health=HealthState.UNAVAILABLE),
    )
    router = DeterministicRouter(reg)
    with pytest.raises(CialError) as exc:
        router.route(
            RoutingRequest(
                policy=RoutingPolicy.MANUAL,
                manual_provider_id="mock",
                manual_model_id="off",
            )
        )
    assert exc.value.code == CialErrorCode.MODEL_DISABLED
    with pytest.raises(CialError) as exc2:
        router.route(
            RoutingRequest(
                policy=RoutingPolicy.MANUAL,
                manual_provider_id="mock",
                manual_model_id="down",
            )
        )
    assert exc2.value.code == CialErrorCode.PROVIDER_UNAVAILABLE


def test_no_eligible_model() -> None:
    reg = _registry(_model("only", health=HealthState.UNAVAILABLE))
    with pytest.raises(CialError) as exc:
        DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.DEFAULT))
    assert exc.value.code == CialErrorCode.ROUTING_FAILED


def test_deterministic_tie_breakers() -> None:
    """Same cost/latency/quality → health preference then provider/model lex order."""
    reg = _registry(
        _model("z-model", provider_id="z-prov", in_cost=1.0, out_cost=1.0),
        _model("a-model", provider_id="a-prov", in_cost=1.0, out_cost=1.0),
        _model(
            "degraded",
            provider_id="a-prov",
            in_cost=1.0,
            out_cost=1.0,
            health=HealthState.DEGRADED,
        ),
    )
    decision = DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.LOWEST_COST))
    assert decision.provider_id == "a-prov"
    assert decision.model_id == "a-model"


def test_degraded_eligible_but_ranked_after_healthy() -> None:
    reg = _registry(
        _model("healthy", health=HealthState.HEALTHY, in_cost=5.0),
        _model("degraded", health=HealthState.DEGRADED, in_cost=1.0),
    )
    # Cost still wins over health when costs differ.
    cheap = DeterministicRouter(reg).route(RoutingRequest(policy=RoutingPolicy.LOWEST_COST))
    assert cheap.model_id == "degraded"
    # Equal cost → healthy preferred.
    reg2 = _registry(
        _model("healthy", health=HealthState.HEALTHY, in_cost=1.0),
        _model("degraded", health=HealthState.DEGRADED, in_cost=1.0),
    )
    tied = DeterministicRouter(reg2).route(RoutingRequest(policy=RoutingPolicy.LOWEST_COST))
    assert tied.model_id == "healthy"
