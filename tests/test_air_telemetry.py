"""KC-023 AIR telemetry, audit correlation, and HTTP API tests."""

from __future__ import annotations

import pytest

from cobra_core.air.audit import AIR_AUDIT, AirAuditLog
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.catalog import build_default_catalog
from cobra_core.air.http_api import handle_air_audit, handle_air_catalog, handle_air_route
from cobra_core.air.metrics import AIR_METRICS, AirMetrics
from cobra_core.air.router import AdaptiveRouter
from cobra_core.air.types import AirRequest
from cobra_core.cial.config import CialConfig
from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.protocol_v1.metrics import MetricsRegistry


@pytest.fixture(autouse=True)
def _reset_global_air() -> None:
    AIR_METRICS.reset()
    AIR_AUDIT.clear()
    yield
    AIR_METRICS.reset()
    AIR_AUDIT.clear()


def test_prometheus_air_metric_names() -> None:
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg, metrics=AIR_METRICS, audit=AIR_AUDIT)
    router.route(
        AirRequest(
            capabilities=frozenset({AirCapability.TEXT, AirCapability.OFFLINE}),
            correlation_id="corr_test_1",
            profile_id="default",
        )
    )
    text = AIR_METRICS.render_prometheus()
    for name in (
        "air_routing_total",
        "air_routing_success_total",
        "air_routing_failure_total",
        "air_provider_selection_total",
        "air_model_selection_total",
        "air_no_capability_match_total",
        "air_provider_unhealthy_total",
        "air_policy_exclusion_total",
        "air_fail_closed_total",
        "air_routing_latency_ms_sum",
        "air_routing_latency_ms_count",
    ):
        assert name in text
    assert 'provider="mock"' in text
    # No unbounded labels
    assert "corr_test_1" not in text
    assert "prompt" not in text


def test_protocol_metrics_includes_air() -> None:
    AIR_METRICS.record_failure(air_code="no_capability_match")
    reg = MetricsRegistry()
    text = reg.render_prometheus()
    assert "air_routing_total" in text
    assert "air_no_capability_match_total" in text


def test_audit_has_correlation_and_selection_reason() -> None:
    reg = build_default_catalog(openai_enabled=False)
    router = AdaptiveRouter(reg, metrics=AirMetrics(), audit=AirAuditLog())
    d = router.route(
        AirRequest(
            capabilities=frozenset({AirCapability.TEXT}),
            correlation_id="corr_abc",
            profile_id="default",
        )
    )
    assert d.correlation_id == "corr_abc"
    entry = router.audit.recent()[-1]
    assert entry["correlation_id"] == "corr_abc"
    assert entry["selection_reason"]
    assert entry["policy_id"]
    assert "prompt" not in entry


def test_http_route_mock_and_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AIR_ENABLED", "true")
    monkeypatch.delenv("CIAL_LIVE_PROVIDER_ENABLED", raising=False)
    cfg = CialConfig(
        enabled=True,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        mock_model=DEFAULT_MODEL,
    )
    st, body = handle_air_route(
        {"capabilities": ["text", "offline"], "budget": "low", "latency": "fast"},
        config=cfg,
        correlation_id="r1",
    )
    assert st == 200
    assert body["ok"] is True
    assert body["decision"]["selected_provider"] == "mock"
    assert body["decision"]["correlation_id"] == "r1"

    st2, body2 = handle_air_route(
        {"capabilities": ["reasoning", "vision"]},
        config=cfg,
        correlation_id="r2",
    )
    assert st2 == 422
    assert body2["error"]["code"] == "no_capability_match"


def test_http_catalog_mock_only_when_live_closed() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        openai_api_key="k",
        mock_model=DEFAULT_MODEL,
    )
    snap = handle_air_catalog(config=cfg)
    assert snap["providers"][0]["provider_id"] == "mock"
    assert len(snap["providers"]) == 1


def test_policy_exclusion_fail_closed() -> None:
    cfg = CialConfig(
        enabled=True,
        active_profile="research",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=True,
        openai_api_key="k",
        openai_model="gpt-5.4-mini",
        mock_model=DEFAULT_MODEL,
    )
    assert cfg.can_use_live_provider
    st, body = handle_air_route(
        {
            "capabilities": ["vision", "reasoning"],
            "excluded_providers": ["openai"],
            "requires_live": True,
            "allow_offline_fallback": False,
        },
        config=cfg,
    )
    assert st == 422
    assert body["error"]["code"] in {
        "policy_excluded",
        "no_capability_match",
        "live_required_unavailable",
    }


def test_audit_lookup() -> None:
    AIR_AUDIT.record_failure(
        profile_id="default",
        capabilities=frozenset({AirCapability.VISION}),
        air_code="no_capability_match",
        message="x",
        timestamp_ms=1,
        correlation_id="look_me_up",
    )
    out = handle_air_audit(correlation_id="look_me_up")
    assert out["count"] == 1
    assert out["entries"][0]["failure_code"] == "no_capability_match"
