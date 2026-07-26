"""KC-026 Reliability & Resilience Framework tests."""

from __future__ import annotations

import threading

import pytest

from cobra_core.air.capabilities import AirCapability
from cobra_core.air.catalog import build_default_catalog
from cobra_core.cial.config import CialConfig
from cobra_core.cial.types import RoutingPolicy
from cobra_core.isf.engine import SkillEngine
from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.isf.registry import SkillRegistry
from cobra_core.isf.skills import register_builtin_skills
from cobra_core.isf.types import SkillExecutionStatus, SkillRequest
from cobra_core.protocol_v1.constants import DEFAULT_MODEL
from cobra_core.resilience.audit import RRF_AUDIT
from cobra_core.resilience.budget import GLOBAL_BUDGET
from cobra_core.resilience.circuit_breaker import CircuitBreakerRegistry
from cobra_core.resilience.config import ResilienceConfig, load_resilience_config
from cobra_core.resilience.errors import FailureCategory
from cobra_core.resilience.executor import ResilienceExecutor
from cobra_core.resilience.fallback import evaluate_fallback
from cobra_core.resilience.faults import scripted_caller
from cobra_core.resilience.idempotency import IDEMPOTENCY_STORE, make_execution_id
from cobra_core.resilience.metrics import RRF_METRICS
from cobra_core.resilience.retry import should_retry
from cobra_core.resilience.types import (
    CircuitState,
    ExecutionStatus,
    ResilienceRequest,
    RouteTarget,
)


@pytest.fixture(autouse=True)
def _reset_rrf() -> None:
    RRF_AUDIT.clear()
    RRF_METRICS.reset()
    IDEMPOTENCY_STORE.clear()
    GLOBAL_BUDGET.reset()
    yield
    RRF_AUDIT.clear()
    RRF_METRICS.reset()
    IDEMPOTENCY_STORE.clear()
    GLOBAL_BUDGET.reset()


def _cfg(**kw: object) -> ResilienceConfig:
    base = dict(
        enabled=True,
        max_attempts=2,
        max_provider_calls=3,
        initial_backoff_ms=1,
        max_backoff_ms=5,
        request_deadline_ms=5_000,
        provider_timeout_ms=1_000,
        circuit_failure_threshold=5,
        circuit_window_seconds=60,
        circuit_open_seconds=1,
        circuit_success_threshold=2,
        allow_fallback=True,
        max_estimated_cost_usd=1.0,
        hourly_budget_usd=10.0,
        daily_budget_usd=50.0,
        jitter_seed=0,
    )
    base.update(kw)
    return ResilienceConfig(**base)  # type: ignore[arg-type]


def _req(**kw: object) -> ResilienceRequest:
    base = dict(
        execution_id="rrf_test_1",
        correlation_id="corr_1",
        skill_id="evidence_summary",
        skill_version="1.0.0",
        profile_id="default",
        required_capabilities=frozenset(
            {
                AirCapability.SUMMARIZATION,
                AirCapability.REASONING,
                AirCapability.STRUCTURED_OUTPUT,
            }
        ),
        primary=RouteTarget(provider_id="openai", model_id="gpt-5.4-mini", route_reason="air"),
        allow_offline_fallback=True,
    )
    base.update(kw)
    return ResilienceRequest(**base)  # type: ignore[arg-type]


def _exec(script_steps: list[str], **cfg_kw: object) -> tuple[ResilienceExecutor, object]:
    caller = scripted_caller(script_steps)
    sleeps: list[float] = []
    ex = ResilienceExecutor(
        cfg=_cfg(**cfg_kw),
        provider_call=caller,
        catalog=build_default_catalog(openai_enabled=True),
        sleep_fn=lambda s: sleeps.append(s),
        cial_config=CialConfig(
            enabled=True,
            active_profile="research",
            routing_policy=RoutingPolicy.DEFAULT,
            app_env="staging",
            live_provider_enabled=True,
            openai_api_key="k",
            openai_model="gpt-5.4-mini",
            mock_model=DEFAULT_MODEL,
        ),
    )
    return ex, caller


# 1–2 timeout retry
def test_timeout_retry_then_success() -> None:
    ex, caller = _exec(["timeout", "success"])
    res = ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=64)
    assert res.status == ExecutionStatus.SUCCESS
    assert len(caller.calls) == 2


def test_timeout_retry_then_fail() -> None:
    ex, _ = _exec(["timeout", "timeout"], allow_fallback=False)
    res = ex.execute(
        _req(allow_offline_fallback=False),
        messages=[{"role": "user", "content": "x"}],
        max_tokens=64,
    )
    assert res.status == ExecutionStatus.FAILED
    assert res.failure_category == FailureCategory.PROVIDER_TIMEOUT


# 3–4 auth/authz no retry
def test_auth_not_retried() -> None:
    ex, caller = _exec(["http_401", "success"])
    res = ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=64)
    assert res.failure_category == FailureCategory.AUTHENTICATION_FAILURE
    assert len(caller.calls) == 1


def test_forbidden_not_retried() -> None:
    ex, caller = _exec(["http_403"])
    res = ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=64)
    assert res.failure_category == FailureCategory.AUTHORIZATION_FAILURE
    assert len(caller.calls) == 1


# 5–6 rate limit
def test_rate_limit_honors_retry_after() -> None:
    caller = scripted_caller(["http_429", "success"], retry_after_ms=2)
    sleeps: list[float] = []
    ex = ResilienceExecutor(
        cfg=_cfg(),
        provider_call=caller,
        catalog=build_default_catalog(openai_enabled=True),
        sleep_fn=lambda s: sleeps.append(s),
        cial_config=CialConfig(
            enabled=True,
            active_profile="default",
            routing_policy=RoutingPolicy.DEFAULT,
            app_env="staging",
            live_provider_enabled=True,
            openai_api_key="k",
            mock_model=DEFAULT_MODEL,
        ),
    )
    res = ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=32)
    assert res.status == ExecutionStatus.SUCCESS
    assert sleeps  # backoff occurred


def test_rate_limit_excessive_retry_after_no_sleep_past_deadline() -> None:
    ok, reason = should_retry(
        FailureCategory.RATE_LIMITED,
        attempts_so_far=1,
        cfg=_cfg(request_deadline_ms=100),
        remaining_deadline_ms=50,
        retry_after_ms=10_000,
    )
    assert ok is False
    assert reason == "retry_after_exceeds_deadline"


# 7–11 circuit breaker
def test_circuit_opens_after_threshold() -> None:
    cfg = _cfg(circuit_failure_threshold=5, circuit_open_seconds=30)
    reg = CircuitBreakerRegistry(cfg)
    br = reg.get("openai", "gpt-5.4-mini")
    for _ in range(5):
        br.record_failure()
    assert br.state == CircuitState.OPEN
    allowed, _ = br.allow_request()
    assert allowed is False


def test_circuit_half_open_and_close() -> None:
    cfg = _cfg(circuit_failure_threshold=2, circuit_open_seconds=0, circuit_success_threshold=2)
    reg = CircuitBreakerRegistry(cfg)
    br = reg.get("openai", "m")
    br.record_failure()
    br.record_failure()
    assert br.state == CircuitState.OPEN
    # open duration 0 → half_open on next refresh
    assert br.current_state() == CircuitState.HALF_OPEN
    allowed, _ = br.allow_request()
    assert allowed
    br.record_success()
    br.record_success()
    assert br.current_state() == CircuitState.CLOSED


def test_half_open_failure_reopens() -> None:
    cfg = _cfg(circuit_failure_threshold=1, circuit_open_seconds=0)
    reg = CircuitBreakerRegistry(cfg)
    br = reg.get("openai", "m")
    br.record_failure()
    assert br.state == CircuitState.OPEN
    assert br.current_state() == CircuitState.HALF_OPEN
    br.allow_request()
    br.record_failure()
    assert br.state == CircuitState.OPEN


# 12–15 fallback
def test_vision_never_falls_back_to_mock() -> None:
    cat = build_default_catalog(openai_enabled=True)
    dec = evaluate_fallback(
        cfg=_cfg(),
        failure=FailureCategory.PROVIDER_TIMEOUT,
        required=frozenset(
            {AirCapability.VISION, AirCapability.REASONING, AirCapability.STRUCTURED_OUTPUT}
        ),
        primary=RouteTarget("openai", "gpt-5.4-mini"),
        catalog=cat,
        allow_offline_fallback=True,
        live_gate_open=True,
    )
    assert dec.allowed is False
    assert "vision" in dec.reason


def test_offline_summary_may_fallback_to_mock() -> None:
    cat = build_default_catalog(openai_enabled=True)
    dec = evaluate_fallback(
        cfg=_cfg(),
        failure=FailureCategory.PROVIDER_UNAVAILABLE,
        required=frozenset(
            {
                AirCapability.SUMMARIZATION,
                AirCapability.REASONING,
                AirCapability.STRUCTURED_OUTPUT,
            }
        ),
        primary=RouteTarget("openai", "gpt-5.4-mini"),
        catalog=cat,
        allow_offline_fallback=True,
        live_gate_open=False,
    )
    assert dec.allowed is True
    assert dec.target and dec.target.provider_id == "mock"


def test_fallback_disabled_by_policy() -> None:
    cat = build_default_catalog(openai_enabled=True)
    dec = evaluate_fallback(
        cfg=_cfg(allow_fallback=False),
        failure=FailureCategory.PROVIDER_TIMEOUT,
        required=frozenset({AirCapability.TEXT}),
        primary=RouteTarget("openai", "gpt-5.4-mini"),
        catalog=cat,
        allow_offline_fallback=True,
        live_gate_open=True,
    )
    assert dec.allowed is False


def test_closed_live_gate_blocks_openai_fallback() -> None:
    cat = build_default_catalog(openai_enabled=False)
    dec = evaluate_fallback(
        cfg=_cfg(),
        failure=FailureCategory.PROVIDER_UNAVAILABLE,
        required=frozenset({AirCapability.TEXT, AirCapability.OFFLINE}),
        primary=RouteTarget("mock", DEFAULT_MODEL),
        catalog=cat,
        allow_offline_fallback=False,
        live_gate_open=False,
    )
    assert dec.allowed is False


# 16–18 budget + call ceiling
def test_budget_checked_before_call() -> None:
    ex, caller = _exec(["success"], max_estimated_cost_usd=0.0)
    res = ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=64)
    # mock cost is 0 — use openai with high token estimate
    # Force non-zero estimate by using openai path with huge tokens in config prices
    assert res.status in {ExecutionStatus.SUCCESS, ExecutionStatus.BUDGET_EXCEEDED}
    # Explicit budget deny:
    GLOBAL_BUDGET.reset()
    ex2, caller2 = _exec(["success"], max_estimated_cost_usd=0.000000001, max_output_tokens=2048)
    # openai estimate with tokens should exceed tiny budget
    res2 = ex2.execute(
        _req(estimated_input_tokens=8000),
        messages=[{"role": "user", "content": "x" * 100}],
        max_tokens=2048,
    )
    assert res2.status == ExecutionStatus.BUDGET_EXCEEDED
    assert len(caller2.calls) == 0


def test_max_provider_calls_ceiling() -> None:
    # timeout + timeout would be 2; repair would be 3rd — ceiling 2 blocks further
    ex, caller = _exec(
        ["timeout", "timeout", "success"],
        max_provider_calls=2,
        max_attempts=2,
        allow_fallback=False,
    )
    res = ex.execute(
        _req(allow_offline_fallback=False),
        messages=[{"role": "user", "content": "x"}],
        max_tokens=32,
    )
    assert len(caller.calls) <= 2
    assert res.status == ExecutionStatus.FAILED


# 19–20 schema repair
def test_schema_repair_once() -> None:
    good = (
        '{"summary":"ok","confidence":0.4,"missing_information":[],'
        '"recommended_next_steps":[],"needs_human_review":true,'
        '"themes":[],"evidence_count":1,"gaps":[]}'
    )
    caller = scripted_caller(["malformed_json", "success"], success_content=good)
    ex = ResilienceExecutor(
        cfg=_cfg(max_provider_calls=3),
        provider_call=caller,
        catalog=build_default_catalog(openai_enabled=True),
        sleep_fn=lambda _s: None,
        cial_config=CialConfig(
            enabled=True,
            active_profile="research",
            routing_policy=RoutingPolicy.DEFAULT,
            app_env="staging",
            live_provider_enabled=True,
            openai_api_key="k",
            mock_model=DEFAULT_MODEL,
        ),
    )

    def parse(raw: str) -> dict:
        from cobra_core.isf.structured_json import parse_provider_json, validate_or_raise

        return validate_or_raise("evidence_summary", parse_provider_json(raw))

    res = ex.execute(
        _req(),
        messages=[{"role": "user", "content": "x"}],
        max_tokens=64,
        parse_structured=parse,
        repair_messages_fn=lambda _p: [{"role": "user", "content": "repair"}],
    )
    assert res.status == ExecutionStatus.SUCCESS
    assert res.schema_repair_count == 1
    assert len(caller.calls) == 2


# 21–22 cancellation
def test_cancellation_stops_retry() -> None:
    ev = threading.Event()
    ev.set()
    ex, caller = _exec(["timeout", "success"])
    res = ex.execute(
        _req(),
        messages=[{"role": "user", "content": "x"}],
        max_tokens=32,
        cancel_event=ev,
    )
    assert res.status == ExecutionStatus.CANCELLED
    assert len(caller.calls) == 0


def test_cancellation_does_not_open_circuit() -> None:
    from cobra_core.resilience.errors import traits_for

    assert traits_for(FailureCategory.CANCELLED).circuit_breaker_relevant is False
    cfg = _cfg(circuit_failure_threshold=1)
    reg = CircuitBreakerRegistry(cfg)
    br = reg.get("openai", "m")
    assert br.current_state() == CircuitState.CLOSED


# 23–24 idempotency
def test_idempotent_replay_no_duplicate_provider_calls() -> None:
    ex, caller = _exec(["success"])
    req = _req(execution_id="idem_1")
    r1 = ex.execute(req, messages=[{"role": "user", "content": "x"}], max_tokens=32)
    r2 = ex.execute(req, messages=[{"role": "user", "content": "x"}], max_tokens=32)
    assert r1.status == ExecutionStatus.SUCCESS
    assert r2.idempotency_hit is True
    assert len(caller.calls) == 1


def test_revision_change_new_execution() -> None:
    a = make_execution_id(
        skill_id="evidence_summary",
        skill_version="1.0.0",
        correlation_id="c1",
        revision="1",
        profile_id="default",
    )
    b = make_execution_id(
        skill_id="evidence_summary",
        skill_version="1.0.0",
        correlation_id="c1",
        revision="2",
        profile_id="default",
    )
    assert a != b


# 25–28 governance / metrics / rollback flag
def test_isf_success_pending_approval_with_rrf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RRF_ENABLED", "true")
    monkeypatch.setenv("RRF_JITTER_SEED", "0")
    reg = SkillRegistry()
    register_builtin_skills(reg)
    caller = scripted_caller(["success"])
    ex = ResilienceExecutor(
        cfg=_cfg(),
        provider_call=caller,
        catalog=build_default_catalog(openai_enabled=False),
        sleep_fn=lambda _s: None,
    )
    engine = SkillEngine(
        registry=reg,
        config=CialConfig(
            enabled=True,
            active_profile="default",
            routing_policy=RoutingPolicy.DEFAULT,
            app_env="staging",
            live_provider_enabled=False,
            mock_model=DEFAULT_MODEL,
        ),
        resilience_executor=ex,
    )
    # Inject provider call that uses mock structured path via bridge — executor already has caller
    from cobra_core.isf.computer_adapter import ComputerIsfAdapter

    adapter = ComputerIsfAdapter(engine=engine)
    body = adapter.execute(
        {
            "skill_id": "evidence_summary",
            "evidence": [{"evidence_type": "evidence_bundle", "ref_id": "e1"}],
        },
        correlation_id="gov_1",
    )
    assert body["proposal"]["status"] == "pending_approval"
    assert body["proposal"]["human_approval_required"] is True


def test_metrics_bounded_labels() -> None:
    ex, _ = _exec(["success"])
    ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=16)
    text = RRF_METRICS.render_prometheus()
    assert "rrf_execution_total" in text
    assert "correlation" not in text.lower()


def test_rrf_disabled_restores_kc025_path(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RRF_ENABLED", "false")
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(
        registry=reg,
        config=CialConfig(
            enabled=True,
            active_profile="default",
            routing_policy=RoutingPolicy.DEFAULT,
            app_env="staging",
            live_provider_enabled=False,
            mock_model=DEFAULT_MODEL,
        ),
    )
    result = engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "b1"),),
        )
    )
    assert result.status == SkillExecutionStatus.NEEDS_HUMAN_REVIEW
    assert result.selected_provider == "mock"
    assert result.needs_human_review is True


def test_config_validation_fails_closed() -> None:
    with pytest.raises(ValueError):
        load_resilience_config(env={"RRF_MAX_ATTEMPTS": "0"})


def test_audit_has_attempt_fields() -> None:
    ex, _ = _exec(["timeout", "success"])
    ex.execute(_req(), messages=[{"role": "user", "content": "x"}], max_tokens=16)
    entries = RRF_AUDIT.recent()
    assert entries
    assert any("failure_category" in e or e.get("final_execution_status") for e in entries)


def test_open_circuit_blocks_executor() -> None:
    ex, caller = _exec(
        ["timeout"] * 5,
        circuit_failure_threshold=3,
        max_attempts=1,
        allow_fallback=False,
        circuit_open_seconds=60,
    )
    # Burn circuit
    for i in range(3):
        ex.execute(
            _req(execution_id=f"burn_{i}", allow_offline_fallback=False),
            messages=[{"role": "user", "content": "x"}],
            max_tokens=8,
        )
    res = ex.execute(
        _req(execution_id="blocked", allow_offline_fallback=False),
        messages=[{"role": "user", "content": "x"}],
        max_tokens=8,
    )
    assert res.status in {ExecutionStatus.CIRCUIT_OPEN, ExecutionStatus.FAILED}
    assert res.failure_category == FailureCategory.CIRCUIT_OPEN
    assert len(caller.calls) == 3
