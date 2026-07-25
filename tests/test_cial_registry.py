"""CIAL registry and configuration unit tests (KC-019 Phase 1)."""

from __future__ import annotations

import pytest

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.config import CialConfigError, load_cial_config
from cobra_core.cial.errors import CialError, CialErrorCode, to_protocol_code
from cobra_core.cial.health import HealthState
from cobra_core.cial.providers.mock import MockProvider
from cobra_core.cial.registry import ModelRegistry, ProviderRegistry
from cobra_core.cial.types import LatencyTier, ModelRecord, QualityTier
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


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
        capabilities=caps
        or frozenset({Capability.TEXT, Capability.JSON, Capability.REASONING, Capability.RESEARCH}),
        context_window=8192,
        max_output_tokens=2048,
        supports_json=True,
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


def test_provider_and_model_registration() -> None:
    providers = ProviderRegistry()
    models = ModelRegistry()
    mock = MockProvider()
    providers.register_provider_models(mock, models)
    assert len(providers) == 1
    assert len(models) == 1
    assert models.get("mock", DEFAULT_MODEL).model_id == DEFAULT_MODEL


def test_duplicate_provider_registration() -> None:
    providers = ProviderRegistry()
    providers.register(MockProvider())
    with pytest.raises(CialError) as exc:
        providers.register(MockProvider())
    assert exc.value.code == CialErrorCode.ROUTING_FAILED


def test_duplicate_model_registration() -> None:
    models = ModelRegistry()
    models.register(_model("a"))
    with pytest.raises(CialError):
        models.register(_model("a"))


def test_model_lookup_and_not_found() -> None:
    models = ModelRegistry()
    models.register(_model("alpha"))
    assert models.get("mock", "alpha").display_name == "alpha"
    with pytest.raises(CialError) as exc:
        models.get("mock", "missing")
    assert exc.value.code == CialErrorCode.MODEL_NOT_FOUND


def test_configuration_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CIAL_ENABLED", raising=False)
    monkeypatch.delenv("CIAL_DEFAULT_PROVIDER", raising=False)
    monkeypatch.delenv("CIAL_DEFAULT_MODEL", raising=False)
    monkeypatch.delenv("CIAL_ROUTING_POLICY", raising=False)
    cfg = load_cial_config()
    assert cfg.enabled is True
    assert cfg.default_provider == "mock"
    assert cfg.default_model == DEFAULT_MODEL
    assert cfg.routing_policy.value == "default"


def test_configuration_invalid_policy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CIAL_ROUTING_POLICY", "not-a-policy")
    with pytest.raises(CialConfigError):
        load_cial_config()


def test_error_translation_to_protocol_codes() -> None:
    assert to_protocol_code(CialErrorCode.MODEL_DISABLED) == "provider_disabled"
    assert to_protocol_code(CialErrorCode.RATE_LIMITED) == "rate_limited"
    assert to_protocol_code(CialErrorCode.INFERENCE_FAILED) == "provider_error"
    assert to_protocol_code(CialErrorCode.CAPABILITY_MISMATCH) == "bad_request"
    assert to_protocol_code("unknown_code") == "provider_error"
