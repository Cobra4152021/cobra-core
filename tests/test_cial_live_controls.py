"""KC-021 live-provider activation controls and guards (no live network)."""

from __future__ import annotations

import pytest

from cial_fakes import FakeTransport
from cial_fakes import completion_body as _completion_body
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.guards import LiveRequestGuard
from cobra_core.cial.health import HealthState
from cobra_core.cial.providers.http_transport import HttpResponse
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.providers.openai_compatible import OpenAICompatibleProvider
from cobra_core.cial.types import LatencyTier, ModelRecord, QualityTier, RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


def _live_cfg(**overrides: object) -> CialConfig:
    base = dict(
        enabled=True,
        default_provider="openai",
        default_model="gpt-test",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=True,
        openai_api_key="test-key",
        openai_model="gpt-test",
        openai_max_retries=0,
        live_max_concurrent=1,
        live_max_input_chars=1000,
        live_daily_request_quota=5,
    )
    base.update(overrides)
    return CialConfig(**base)  # type: ignore[arg-type]


def test_live_flag_defaults_false(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CIAL_LIVE_PROVIDER_ENABLED", raising=False)
    monkeypatch.delenv("CIAL_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    cfg = load_cial_config()
    assert cfg.live_provider_enabled is False
    assert cfg.can_use_live_provider is False


def test_live_requires_all_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("CIAL_ENABLED", "true")
    monkeypatch.setenv("CIAL_LIVE_PROVIDER_ENABLED", "true")
    monkeypatch.setenv("CIAL_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    assert load_cial_config().can_use_live_provider is True

    monkeypatch.setenv("APP_ENV", "production")
    assert load_cial_config().can_use_live_provider is False

    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("CIAL_LIVE_PROVIDER_ENABLED", "false")
    assert load_cial_config().can_use_live_provider is False


def test_build_default_registers_openai_only_when_live_ready() -> None:
    off = CialEngine.build_default(_live_cfg(live_provider_enabled=False))
    assert len(off.providers) == 1
    assert off.providers.get("mock").provider_id == "mock"

    on = CialEngine.build_default(_live_cfg())
    assert len(on.providers) == 2
    assert on.providers.get("openai").provider_id == "openai"


def test_openai_selection_forced_to_mock_when_live_disabled() -> None:
    cfg = _live_cfg(live_provider_enabled=False)
    engine = CialEngine(config=cfg)
    engine.providers.register_provider_models(MockProvider(model_id=DEFAULT_MODEL), engine.models)
    result = engine.complete([{"role": "user", "content": "rollback"}], 16)
    assert result.content.startswith("[mock] rollback")
    assert result.cial_provider_id == "mock"
    assert result.cial_route_reason == "live_provider_disabled_use_mock"


def test_live_engine_uses_openai_when_enabled() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body("live-ok"), {})])
    cfg = _live_cfg()
    engine = CialEngine(config=cfg)
    engine.providers.register_provider_models(MockProvider(model_id=DEFAULT_MODEL), engine.models)
    openai = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=0
    )
    openai.set_health(HealthState.HEALTHY)
    engine.providers.register_provider_models(openai, engine.models)
    result = engine.complete(
        [{"role": "user", "content": "hi"}],
        16,
        preferred_model_id=DEFAULT_MODEL,
    )
    assert result.content == "live-ok"
    assert result.cial_provider_id == "openai"


def test_guard_input_and_quota() -> None:
    cfg = _live_cfg(live_max_input_chars=10, live_daily_request_quota=1)
    guard = LiveRequestGuard(cfg)
    model = ModelRecord(
        provider_id="openai",
        model_id="gpt-test",
        display_name="t",
        enabled=True,
        capabilities=frozenset(),
        context_window=1,
        max_output_tokens=16,
        supports_json=True,
        supports_tools=False,
        supports_vision=False,
        supports_streaming=False,
        quality_tier=QualityTier.STANDARD,
        latency_tier=LatencyTier.STANDARD,
        estimated_input_cost=0.001,
        estimated_output_cost=0.002,
        revision="t",
    )
    with pytest.raises(CialError) as exc:
        guard.acquire(input_chars=50, max_tokens=8, model=model)
    assert exc.value.code == CialErrorCode.QUOTA_EXCEEDED

    guard.acquire(input_chars=5, max_tokens=8, model=model)
    guard.release(prompt_tokens=5, completion_tokens=2, model=model)
    with pytest.raises(CialError) as exc2:
        guard.acquire(input_chars=5, max_tokens=8, model=model)
    assert exc2.value.code == CialErrorCode.QUOTA_EXCEEDED


def test_cost_ceiling_fail_closed() -> None:
    cfg = _live_cfg(live_daily_cost_ceiling=0.0001, live_daily_request_quota=None)
    guard = LiveRequestGuard(cfg)
    model = ModelRecord(
        provider_id="openai",
        model_id="gpt-test",
        display_name="t",
        enabled=True,
        capabilities=frozenset(),
        context_window=1,
        max_output_tokens=16,
        supports_json=True,
        supports_tools=False,
        supports_vision=False,
        supports_streaming=False,
        quality_tier=QualityTier.STANDARD,
        latency_tier=LatencyTier.STANDARD,
        estimated_input_cost=10.0,
        estimated_output_cost=10.0,
        revision="t",
    )
    with pytest.raises(CialError) as exc:
        guard.acquire(input_chars=100, max_tokens=100, model=model)
    assert exc.value.code == CialErrorCode.QUOTA_EXCEEDED
