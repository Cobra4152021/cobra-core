"""KC-022 Adaptive Intelligence Router — routing matrix and policy tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.air.audit import AirAuditLog
from cobra_core.air.bridge import (
    air_request_for_config,
    build_adaptive_router,
    catalog_for_config,
)
from cobra_core.air.capabilities import AirCapability, parse_air_capabilities
from cobra_core.air.catalog import build_default_catalog
from cobra_core.air.errors import AirRoutingError, AirRoutingFailureCode
from cobra_core.air.metrics import AirMetrics
from cobra_core.air.policy import AirPolicyConfig, load_air_policy_from_dict
from cobra_core.air.profiles import (
    PROFILE_CODING,
    PROFILE_DEFAULT,
    PROFILE_RESEARCH,
    air_request_from_contract,
    air_request_from_profile,
    get_air_profile,
)
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.router import AdaptiveRouter
from cobra_core.air.types import (
    AirRequest,
    BudgetClass,
    CostClass,
    LatencyClass,
    ModelDescriptor,
    PriorityClass,
    ProviderDescriptor,
)
from cobra_core.cial.config import CialConfig
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.health import HealthState
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


def _model(
    provider_id: str,
    model_id: str,
    *caps: AirCapability,
    cost: CostClass = CostClass.NORMAL,
    latency: LatencyClass = LatencyClass.NORMAL,
    health: HealthState = HealthState.HEALTHY,
    requires_live: bool = False,
) -> ModelDescriptor:
    return ModelDescriptor(
        provider_id=provider_id,
        model_id=model_id,
        capabilities=frozenset(caps),
        estimated_cost=cost,
        latency=latency,
        health=health,
        requires_live=requires_live,
    )


def _registry(*models: ModelDescriptor) -> DescriptorRegistry:
    reg = DescriptorRegistry()
    by_provider: dict[str, list[ModelDescriptor]] = {}
    for m in models:
        by_provider.setdefault(m.provider_id, []).append(m)
    for pid, models_list in by_provider.items():
        reg.register_provider(
            ProviderDescriptor(
                provider_id=pid,
                display_name=pid,
                models=tuple(models_list),
            )
        )
    return reg


# --- Capability catalog -------------------------------------------------


def test_parse_initial_capabilities() -> None:
    caps = parse_air_capabilities(["reasoning", "vision", "OCR"])
    assert AirCapability.REASONING in caps
    assert AirCapability.VISION in caps
    assert AirCapability.OCR in caps


def test_unknown_capability_rejected() -> None:
    with pytest.raises(ValueError, match="unknown AIR capability"):
        parse_air_capabilities(["telepathy"])


# --- Profiles as requirements -------------------------------------------


def test_profiles_do_not_bind_vendors_in_air_request() -> None:
    req = air_request_from_profile(PROFILE_RESEARCH)
    assert "openai" not in req.task
    assert req.metadata.get("requires_live") is True
    assert AirCapability.REASONING in req.capabilities
    # Request contract has no provider/model fields
    assert not hasattr(req, "provider_id")
    assert not hasattr(req, "model_id")


def test_capability_contract_shape() -> None:
    req = air_request_from_contract(
        task="investigation",
        capabilities=["reasoning", "vision"],
        priority="normal",
        budget="low",
        latency="normal",
        profile_id="research",
    )
    assert req.task == "investigation"
    assert req.budget == BudgetClass.LOW
    assert AirCapability.VISION in req.capabilities


# --- Routing matrix -----------------------------------------------------


def test_offline_capability_selects_mock() -> None:
    reg = build_default_catalog(openai_enabled=True)
    router = AdaptiveRouter(reg)
    decision = router.route(air_request_from_profile(PROFILE_DEFAULT))
    assert decision.provider_id == "mock"
    assert decision.model_id == DEFAULT_MODEL


def test_vision_requires_openai_when_available() -> None:
    reg = build_default_catalog(openai_enabled=True, openai_model_id="gpt-5.4-mini")
    router = AdaptiveRouter(reg)
    req = AirRequest(
        task="investigation",
        capabilities=frozenset({AirCapability.VISION, AirCapability.REASONING}),
        profile_id="research",
        metadata={"requires_live": True, "allow_offline_fallback": False},
    )
    decision = router.route(req)
    assert decision.provider_id == "openai"
    assert decision.model_id == "gpt-5.4-mini"


def test_vision_fail_closed_without_capable_provider() -> None:
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg)
    req = AirRequest(
        capabilities=frozenset({AirCapability.VISION}),
        profile_id="research",
    )
    with pytest.raises(AirRoutingError) as exc:
        router.route(req)
    assert exc.value.air_code == AirRoutingFailureCode.NO_CAPABILITY_MATCH


def test_research_prefers_live_when_registered() -> None:
    reg = build_default_catalog(openai_enabled=True, openai_model_id="gpt-live")
    router = AdaptiveRouter(reg)
    req = air_request_from_profile(PROFILE_RESEARCH)
    # requires_live True → prefer openai over mock despite mock being faster
    decision = router.route(req)
    assert decision.provider_id == "openai"
    assert "live_preferred" in decision.reason


def test_research_offline_fallback_when_live_absent() -> None:
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg)
    req = air_request_from_profile(PROFILE_RESEARCH)
    # clear requires_live as bridge does when gate closed
    req = AirRequest(
        task=req.task,
        capabilities=req.capabilities,
        priority=req.priority,
        budget=req.budget,
        latency=req.latency,
        profile_id=req.profile_id,
        metadata={"requires_live": False, "allow_offline_fallback": True},
    )
    decision = router.route(req)
    assert decision.provider_id == "mock"


def test_health_excludes_unavailable() -> None:
    reg = _registry(
        _model(
            "a",
            "fast",
            AirCapability.TEXT,
            health=HealthState.UNAVAILABLE,
            cost=CostClass.LOW,
            latency=LatencyClass.FAST,
        ),
        _model(
            "b",
            "ok",
            AirCapability.TEXT,
            health=HealthState.HEALTHY,
            cost=CostClass.NORMAL,
            latency=LatencyClass.NORMAL,
        ),
    )
    router = AdaptiveRouter(reg)
    decision = router.route(
        AirRequest(capabilities=frozenset({AirCapability.TEXT}), profile_id="default")
    )
    assert decision.provider_id == "b"


def test_health_fail_closed_when_all_unhealthy() -> None:
    reg = _registry(
        _model(
            "a",
            "x",
            AirCapability.TEXT,
            health=HealthState.UNAVAILABLE,
        )
    )
    router = AdaptiveRouter(reg)
    with pytest.raises(AirRoutingError) as exc:
        router.route(AirRequest(capabilities=frozenset({AirCapability.TEXT})))
    assert exc.value.air_code == AirRoutingFailureCode.NO_HEALTHY_CANDIDATE


def test_cost_preference_within_budget() -> None:
    reg = _registry(
        _model(
            "cheap",
            "c1",
            AirCapability.CODING,
            cost=CostClass.LOW,
            latency=LatencyClass.SLOW,
        ),
        _model(
            "pricey",
            "p1",
            AirCapability.CODING,
            cost=CostClass.HIGH,
            latency=LatencyClass.FAST,
        ),
    )
    router = AdaptiveRouter(reg, policy=AirPolicyConfig(provider_preference={}))
    decision = router.route(
        AirRequest(
            capabilities=frozenset({AirCapability.CODING}),
            budget=BudgetClass.LOW,
            latency=LatencyClass.NORMAL,
        )
    )
    assert decision.provider_id == "cheap"


def test_latency_preference() -> None:
    reg = _registry(
        _model(
            "slow",
            "s1",
            AirCapability.SUMMARIZATION,
            cost=CostClass.LOW,
            latency=LatencyClass.SLOW,
        ),
        _model(
            "fast",
            "f1",
            AirCapability.SUMMARIZATION,
            cost=CostClass.LOW,
            latency=LatencyClass.FAST,
        ),
    )
    router = AdaptiveRouter(reg, policy=AirPolicyConfig(provider_preference={}))
    decision = router.route(
        AirRequest(
            capabilities=frozenset({AirCapability.SUMMARIZATION}),
            budget=BudgetClass.HIGH,
            latency=LatencyClass.FAST,
        )
    )
    assert decision.provider_id == "fast"


def test_policy_exclusion() -> None:
    reg = build_default_catalog(openai_enabled=True)
    policy = AirPolicyConfig(excluded_providers=frozenset({"openai"}))
    router = AdaptiveRouter(reg, policy=policy)
    req = AirRequest(
        capabilities=frozenset({AirCapability.VISION}),
        metadata={"requires_live": True, "allow_offline_fallback": False},
    )
    with pytest.raises(AirRoutingError) as exc:
        router.route(req)
    assert exc.value.air_code in {
        AirRoutingFailureCode.POLICY_EXCLUDED,
        AirRoutingFailureCode.NO_CAPABILITY_MATCH,
        AirRoutingFailureCode.LIVE_REQUIRED_UNAVAILABLE,
    }


def test_stable_tiebreak_lexicographic() -> None:
    reg = _registry(
        _model("zeta", "z", AirCapability.TEXT, cost=CostClass.LOW, latency=LatencyClass.FAST),
        _model("alpha", "a", AirCapability.TEXT, cost=CostClass.LOW, latency=LatencyClass.FAST),
    )
    router = AdaptiveRouter(reg, policy=AirPolicyConfig(provider_preference={}))
    d1 = router.route(AirRequest(capabilities=frozenset({AirCapability.TEXT})))
    d2 = router.route(AirRequest(capabilities=frozenset({AirCapability.TEXT})))
    assert d1.provider_id == d2.provider_id == "alpha"


# --- Audit / metrics ----------------------------------------------------


def test_audit_records_safe_fields_not_prompts() -> None:
    audit = AirAuditLog()
    metrics = AirMetrics()
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg, audit=audit, metrics=metrics)
    router.route(air_request_from_profile(PROFILE_DEFAULT))
    entries = audit.recent()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["selected_provider"] == "mock"
    assert "requested_capabilities" in entry
    assert "prompt" not in entry
    assert "messages" not in entry
    snap = metrics.snapshot()
    assert snap["routing_count"] == 1
    assert snap["provider_selections"]["mock"] == 1


def test_audit_failure_recorded() -> None:
    audit = AirAuditLog()
    metrics = AirMetrics()
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg, audit=audit, metrics=metrics)
    with pytest.raises(AirRoutingError):
        router.route(AirRequest(capabilities=frozenset({AirCapability.AUDIO})))
    assert metrics.snapshot()["routing_failures"] == 1
    assert audit.recent()[-1]["failure_code"] == "no_capability_match"


# --- Policy config without code changes ---------------------------------


def test_policy_from_json_file(tmp_path: Path) -> None:
    path = tmp_path / "air_policy.json"
    path.write_text(
        json.dumps(
            {
                "policy_id": "ops_v1",
                "provider_preference": {"mock": 1, "openai": 99},
                "excluded_providers": [],
            }
        ),
        encoding="utf-8",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    policy = load_air_policy_from_dict(data)
    assert policy.policy_id == "ops_v1"
    assert policy.provider_preference["mock"] == 1


# --- Bridge / engine regression -----------------------------------------


def test_bridge_catalog_hides_openai_when_live_closed() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        openai_api_key="k",
        openai_model="gpt-x",
        mock_model=DEFAULT_MODEL,
    )
    cat = catalog_for_config(cfg)
    assert len(cat.list_providers()) == 1
    assert cat.list_providers()[0].provider_id == "mock"


def test_bridge_catalog_includes_openai_when_live_open() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=True,
        openai_api_key="k",
        openai_model="gpt-x",
        mock_model=DEFAULT_MODEL,
    )
    cat = catalog_for_config(cfg)
    ids = {p.provider_id for p in cat.list_providers()}
    assert ids == {"mock", "openai"}


def test_engine_air_default_mock_regression() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        mock_model=DEFAULT_MODEL,
    )
    engine = CialEngine.build_default(cfg)
    result = engine.complete([{"role": "user", "content": "kc022"}], 16)
    assert result.content.startswith("[mock] kc022")
    assert result.cial_provider_id == "mock"
    assert result.cial_route_reason.startswith("air_v1")


def test_engine_research_offline_fallback_reason() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        openai_api_key="k",
        openai_model="gpt-x",
        mock_model=DEFAULT_MODEL,
    )
    engine = CialEngine.build_default(cfg)
    result = engine.complete([{"role": "user", "content": "fallback"}], 16)
    assert result.cial_provider_id == "mock"
    assert result.cial_route_reason == "profile_live_unavailable_use_offline"
    assert result.cial_profile == "research"


def test_coding_profile_routes() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile=PROFILE_CODING,
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        mock_model=DEFAULT_MODEL,
    )
    router = build_adaptive_router(cfg)
    decision = router.route(air_request_for_config(cfg))
    assert decision.provider_id == "mock"
    assert get_air_profile(PROFILE_CODING).profile_id == PROFILE_CODING


def test_air_request_for_config_clears_live_when_gate_closed() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile=PROFILE_RESEARCH,
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        openai_api_key="k",
        openai_model="gpt-x",
        mock_model=DEFAULT_MODEL,
    )
    req = air_request_for_config(cfg)
    assert req.metadata.get("requires_live") is False
    assert req.metadata.get("live_gate_closed") is True
