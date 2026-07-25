"""KC-020 OpenAI-compatible provider tests (no live network)."""

from __future__ import annotations

import pytest

from cial_fakes import FakeTransport
from cial_fakes import completion_body as _completion_body
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.health import HealthState
from cobra_core.cial.providers.http_transport import HttpResponse
from cobra_core.cial.providers.openai_compatible import (
    OpenAICompatibleProvider,
    map_http_status_to_cial,
)
from cobra_core.cial.registry import ModelRegistry, ProviderRegistry
from cobra_core.cial.router import DeterministicRouter
from cobra_core.cial.types import GenerateRequest, RoutingPolicy, RoutingRequest
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


def test_map_http_status_taxonomy() -> None:
    assert map_http_status_to_cial(401) == CialErrorCode.AUTHENTICATION_FAILED
    assert map_http_status_to_cial(403) == CialErrorCode.AUTHENTICATION_FAILED
    assert map_http_status_to_cial(404) == CialErrorCode.MODEL_NOT_FOUND
    assert map_http_status_to_cial(408) == CialErrorCode.TIMEOUT
    assert map_http_status_to_cial(429) == CialErrorCode.RATE_LIMITED
    for status in (500, 502, 503, 504):
        assert map_http_status_to_cial(status) == CialErrorCode.PROVIDER_UNAVAILABLE


def test_generate_chat_completion_success() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body("hi there"), {})])
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model_id="gpt-test",
        transport=transport,
        max_retries=0,
    )
    provider.set_health(HealthState.HEALTHY)
    result = provider.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=32,
            model_id="gpt-test",
        )
    )
    assert result.content == "hi there"
    assert result.prompt_tokens == 3
    assert result.completion_tokens == 2
    assert result.cial_provider_id == "openai"
    assert b'"stream":false' in (transport.calls[0]["body"] or b"")
    assert transport.calls[0]["auth_redacted"] is True


def test_json_mode_payload() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body('{"a":1}'), {})])
    provider = OpenAICompatibleProvider(
        api_key="test-key", model_id="gpt-test", transport=transport, max_retries=0
    )
    provider.set_health(HealthState.HEALTHY)
    provider.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "json please"}],
            max_tokens=16,
            model_id="gpt-test",
            metadata={"json_mode": True},
        )
    )
    body = transport.calls[0]["body"] or b""
    assert b'"response_format"' in body
    assert b"json_object" in body


def test_gpt5_uses_max_completion_tokens() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body("pong"), {})])
    provider = OpenAICompatibleProvider(
        api_key="test-key",
        model_id="gpt-5.4-mini",
        transport=transport,
        max_retries=0,
    )
    provider.set_health(HealthState.HEALTHY)
    provider.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=16,
            model_id="gpt-5.4-mini",
        )
    )
    body = transport.calls[0]["body"] or b""
    assert b"max_completion_tokens" in body
    assert b'"max_tokens"' not in body


def test_health_probe_states() -> None:
    healthy = FakeTransport([HttpResponse(200, b'{"data":[]}', {})])
    p = OpenAICompatibleProvider(api_key="k", transport=healthy, max_retries=0)
    assert p.probe_health() == HealthState.HEALTHY

    degraded = FakeTransport([HttpResponse(429, b"{}", {})])
    p2 = OpenAICompatibleProvider(api_key="k", transport=degraded, max_retries=0)
    assert p2.probe_health() == HealthState.DEGRADED

    unavail = FakeTransport([HttpResponse(503, b"{}", {})])
    p3 = OpenAICompatibleProvider(api_key="k", transport=unavail, max_retries=0)
    assert p3.probe_health() == HealthState.UNAVAILABLE

    no_key = OpenAICompatibleProvider(api_key="", transport=FakeTransport(), max_retries=0)
    assert no_key.probe_health() == HealthState.DISABLED


def test_failure_mapping_and_retries() -> None:
    transport = FakeTransport(
        [
            HttpResponse(503, b"{}", {}),
            HttpResponse(200, _completion_body("recovered"), {}),
        ]
    )
    provider = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=1
    )
    provider.set_health(HealthState.HEALTHY)
    result = provider.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
        )
    )
    assert result.content == "recovered"
    assert len(transport.calls) == 2

    auth_t = FakeTransport([HttpResponse(401, b"{}", {})])
    auth_p = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=auth_t, max_retries=3
    )
    auth_p.set_health(HealthState.HEALTHY)
    with pytest.raises(CialError) as exc:
        auth_p.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
            )
        )
    assert exc.value.code == CialErrorCode.AUTHENTICATION_FAILED
    assert len(auth_t.calls) == 1  # no retry on 401


def test_invalid_json_and_schema() -> None:
    bad_json = FakeTransport([HttpResponse(200, b"not-json", {})])
    p = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=bad_json, max_retries=0
    )
    p.set_health(HealthState.HEALTHY)
    with pytest.raises(CialError) as exc:
        p.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
            )
        )
    assert exc.value.code == CialErrorCode.INVALID_RESPONSE

    bad_schema = FakeTransport([HttpResponse(200, b'{"choices":[]}', {})])
    p2 = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=bad_schema, max_retries=0
    )
    p2.set_health(HealthState.HEALTHY)
    with pytest.raises(CialError) as exc2:
        p2.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
            )
        )
    assert exc2.value.code == CialErrorCode.INVALID_RESPONSE


def test_connection_failure() -> None:
    transport = FakeTransport([OSError("connection refused")])
    p = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=0
    )
    p.set_health(HealthState.HEALTHY)
    with pytest.raises(CialError) as exc:
        p.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
            )
        )
    assert exc.value.code == CialErrorCode.PROVIDER_UNAVAILABLE


def test_timeout_failure() -> None:
    transport = FakeTransport([TimeoutError()])
    p = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=0
    )
    p.set_health(HealthState.HEALTHY)
    with pytest.raises(CialError) as exc:
        p.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}], max_tokens=8, model_id="gpt-test"
            )
        )
    assert exc.value.code == CialErrorCode.TIMEOUT


def test_config_defaults_remain_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CIAL_PROFILE", raising=False)
    monkeypatch.delenv("CIAL_PROVIDER", raising=False)
    monkeypatch.delenv("CIAL_DEFAULT_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    cfg = load_cial_config()
    assert cfg.active_profile == "default"
    assert cfg.default_provider == "mock"
    assert cfg.default_model == DEFAULT_MODEL
    assert cfg.openai_configured is False
    assert "test-key" not in repr(cfg)


def test_config_openai_optional_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIAL_PROFILE", "research")
    monkeypatch.setenv("OPENAI_API_KEY", "secret-should-not-appear-in-repr")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-test")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "12.5")
    monkeypatch.setenv("OPENAI_MAX_RETRIES", "3")
    cfg = load_cial_config()
    assert cfg.active_profile == "research"
    assert cfg.default_provider == "openai"
    assert cfg.openai_model == "gpt-test"
    assert cfg.openai_timeout_seconds == 12.5
    assert cfg.openai_max_retries == 3
    assert cfg.default_model == "gpt-test"
    text = repr(cfg)
    assert "secret-should-not-appear-in-repr" not in text
    assert "openai_api_key=<set>" in text


def test_router_selects_mock_vs_openai() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body("from-openai"), {})])
    openai = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=0
    )
    openai.set_health(HealthState.HEALTHY)
    providers = ProviderRegistry()
    models = ModelRegistry()
    from cobra_core.cial.providers.mock import MockProvider

    providers.register_provider_models(MockProvider(model_id=DEFAULT_MODEL), models)
    providers.register_provider_models(openai, models)
    router = DeterministicRouter(models)

    mock_decision = router.route(
        RoutingRequest(policy=RoutingPolicy.DEFAULT, preferred_model_id=DEFAULT_MODEL)
    )
    assert mock_decision.provider_id == "mock"

    openai_decision = router.route(
        RoutingRequest(
            policy=RoutingPolicy.MANUAL,
            manual_provider_id="openai",
            manual_model_id="gpt-test",
        )
    )
    assert openai_decision.provider_id == "openai"


def test_engine_routes_openai_when_configured() -> None:
    transport = FakeTransport([HttpResponse(200, _completion_body("engine-openai"), {})])
    cfg = CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=True,
        openai_api_key="k",
        openai_model="gpt-test",
        openai_max_retries=0,
        mock_model=DEFAULT_MODEL,
    )
    engine = CialEngine(config=cfg)
    from cobra_core.cial.providers.mock import MockProvider

    engine.providers.register_provider_models(MockProvider(model_id=DEFAULT_MODEL), engine.models)
    openai = OpenAICompatibleProvider(
        api_key="k", model_id="gpt-test", transport=transport, max_retries=0
    )
    openai.set_health(HealthState.HEALTHY)
    engine.providers.register_provider_models(openai, engine.models)

    result = engine.complete(
        [{"role": "user", "content": "hi"}],
        16,
        preferred_model_id=DEFAULT_MODEL,  # Protocol wire identity must not force mock
    )
    assert result.content == "engine-openai"
    assert result.cial_provider_id == "openai"
    assert result.cial_model_id == "gpt-test"


def test_build_default_keeps_mock_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("CIAL_PROFILE", "default")
    engine = CialEngine.build_default()
    assert len(engine.providers) == 1
    assert engine.providers.get("mock").provider_id == "mock"
    result = engine.complete([{"role": "user", "content": "alpha"}], 16)
    assert result.content.startswith("[mock] alpha")
    assert result.cial_profile == "default"


def test_repr_does_not_leak_api_key() -> None:
    p = OpenAICompatibleProvider(api_key="super-secret-key", model_id="gpt-test")
    assert "super-secret-key" not in repr(p)
