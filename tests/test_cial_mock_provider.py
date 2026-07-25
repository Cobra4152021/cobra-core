"""CIAL mock provider and InferenceService integration (KC-019 Phase 1)."""

from __future__ import annotations

import pytest

from cobra_core.cial.config import CialConfig
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.types import GenerateRequest, RoutingPolicy
from cobra_core.protocol_v1.config import load_config
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.protocol_v1.inference_service import InferenceService
from cobra_core.protocol_v1.runtime_state import RuntimeState


def test_mock_provider_generation() -> None:
    provider = MockProvider()
    result = provider.generate(
        GenerateRequest(
            messages=[{"role": "user", "content": "hello cial"}],
            max_tokens=64,
            model_id=DEFAULT_MODEL,
        )
    )
    assert result.content.startswith("[mock] hello cial")
    assert result.cial_provider_id == "mock"
    assert result.cial_model_id == DEFAULT_MODEL
    assert result.prompt_tokens > 0
    assert result.completion_tokens > 0


def test_mock_provider_fail_hook() -> None:
    provider = MockProvider()
    with pytest.raises(CialError) as exc:
        provider.generate(
            GenerateRequest(
                messages=[{"role": "user", "content": "x"}],
                max_tokens=16,
                model_id=DEFAULT_MODEL,
                fail=True,
            )
        )
    assert exc.value.code == CialErrorCode.INFERENCE_FAILED


def test_cial_engine_default_route_preserves_identity() -> None:
    engine = CialEngine.build_default()
    result = engine.complete(
        [{"role": "user", "content": "probe"}],
        32,
        preferred_model_id=DEFAULT_MODEL,
    )
    assert result.content.startswith("[mock] probe")
    assert result.cial_provider_id == "mock"
    assert result.cial_model_id == DEFAULT_MODEL
    assert result.cial_routing_policy == RoutingPolicy.DEFAULT.value
    assert result.cial_fallback_count == 0


def test_inference_service_uses_cial_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    monkeypatch.setenv("CIAL_ENABLED", "true")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    svc = InferenceService(cfg, state)
    outcome = svc.complete([{"role": "user", "content": "service path"}], 32)
    assert outcome.ok is True
    assert outcome.result is not None
    assert outcome.result.content.startswith("[mock] service path")
    assert outcome.cial_provider_id == "mock"
    assert outcome.cial_model_id == DEFAULT_MODEL
    assert outcome.cial_routing_policy == "default"


def test_inference_service_cial_disabled_escape(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    cial_cfg = CialConfig(
        enabled=False,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        mock_model=DEFAULT_MODEL,
    )
    svc = InferenceService(cfg, state, cial_config=cial_cfg)
    outcome = svc.complete([{"role": "user", "content": "legacy"}], 32)
    assert outcome.ok is True
    assert outcome.result is not None
    assert outcome.result.content.startswith("[mock] legacy")
    assert outcome.cial_provider_id is None


def test_force_fail_still_maps_provider_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "test-secret")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    svc = InferenceService(cfg, state)
    svc._force_fail = True  # noqa: SLF001 — existing test hook
    outcome = svc.complete([{"role": "user", "content": "boom"}], 16)
    assert outcome.ok is False
    assert outcome.error_code == "provider_error"
