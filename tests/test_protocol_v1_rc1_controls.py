"""RC1 process controls: kill switch, admission, metrics, offline soak (mock only)."""

from __future__ import annotations

import threading
import time

import pytest

from cobra_core.protocol_v1.admission import AdmissionController
from cobra_core.protocol_v1.config import load_config
from cobra_core.protocol_v1.handlers import handle_chat_completions
from cobra_core.protocol_v1.inference_service import InferenceService
from cobra_core.protocol_v1.metrics import MetricsRegistry
from cobra_core.protocol_v1.runtime_state import RuntimeState


@pytest.fixture()
def base_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "rc1-secret")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    monkeypatch.setenv("COBRA_CORE_REVISION", "rc1-test")
    monkeypatch.setenv("COBRA_CORE_GIT_SHA", "deadbeefcafe")
    monkeypatch.setenv("COBRA_CORE_MAX_OUTPUT_TOKENS", "32")
    monkeypatch.setenv("COBRA_CORE_TIMEOUT_MS", "5000")
    monkeypatch.setenv("COBRA_CORE_HOST", "127.0.0.1")
    monkeypatch.setenv("COBRA_CORE_PORT", "18766")
    monkeypatch.setenv("COBRA_PROTOCOL_VERSION", "1")
    monkeypatch.setenv("COBRA_COMPATIBILITY_VERSION", "1")
    monkeypatch.setenv("COBRA_CORE_ENABLED", "true")
    monkeypatch.setenv("COBRA_CORE_MAX_CONCURRENT", "1")
    monkeypatch.setenv("COBRA_INFERENCE_MOCK_DELAY_MS", "0")


def _payload() -> dict:
    return {
        "model": "cobra-core-qwen3-8b",
        "stream": False,
        "max_tokens": 16,
        "messages": [{"role": "user", "content": "ping"}],
    }


def test_kill_switch_disables_completions(base_env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_ENABLED", "false")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    metrics = MetricsRegistry()
    svc = InferenceService(cfg, state, metrics=metrics)
    status, body, _rid = handle_chat_completions(
        cfg,
        authorization="Bearer rc1-secret",
        request_id_header="cc_kill",
        payload=_payload(),
        state=state,
        service=svc,
    )
    assert status == 503
    assert body["code"] == "provider_disabled"
    assert metrics.kill_switch_blocks == 1


def test_concurrency_limit_rejects_second_inflight(
    base_env, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("COBRA_CORE_MAX_CONCURRENT", "1")
    monkeypatch.setenv("COBRA_INFERENCE_MOCK_DELAY_MS", "200")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    metrics = MetricsRegistry()
    svc = InferenceService(cfg, state, metrics=metrics)

    results: list[tuple[int, str]] = []

    def run_one(tag: str) -> None:
        status, body, _ = handle_chat_completions(
            cfg,
            authorization="Bearer rc1-secret",
            request_id_header=f"cc_{tag}",
            payload=_payload(),
            state=state,
            service=svc,
        )
        results.append((status, str(body.get("code", "ok"))))

    t1 = threading.Thread(target=run_one, args=("a",))
    t1.start()
    time.sleep(0.05)
    run_one("b")
    t1.join(timeout=5)
    assert any(code == "rate_limited" for _, code in results)
    assert any(status == 200 for status, _ in results)
    assert svc.admission.active == 0


def test_daily_quota(base_env, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_DAILY_REQUEST_LIMIT", "2")
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    metrics = MetricsRegistry()
    svc = InferenceService(cfg, state, metrics=metrics)
    for i in range(2):
        status, body, _ = handle_chat_completions(
            cfg,
            authorization="Bearer rc1-secret",
            request_id_header=f"cc_q{i}",
            payload=_payload(),
            state=state,
            service=svc,
        )
        assert status == 200, body
    status, body, _ = handle_chat_completions(
        cfg,
        authorization="Bearer rc1-secret",
        request_id_header="cc_q2",
        payload=_payload(),
        state=state,
        service=svc,
    )
    assert status == 429
    assert body["code"] == "rate_limited"
    assert metrics.rate_limited >= 1


def test_admission_controller_unit() -> None:
    ctl = AdmissionController(max_concurrent=2, daily_request_limit=3)
    assert ctl.try_acquire().allowed
    assert ctl.try_acquire().allowed
    denied = ctl.try_acquire()
    assert not denied.allowed
    ctl.release()
    assert ctl.try_acquire().allowed
    ctl.release()
    ctl.release()
    ctl.release()


def test_offline_soak_mock_100_requests(base_env) -> None:
    cfg = load_config()
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    metrics = MetricsRegistry()
    # Raise concurrency for soak throughput; still mock-only.
    svc = InferenceService(
        cfg,
        state,
        admission=AdmissionController(max_concurrent=4, daily_request_limit=1000),
        metrics=metrics,
    )
    ok = 0
    for i in range(100):
        status, _body, _ = handle_chat_completions(
            cfg,
            authorization="Bearer rc1-secret",
            request_id_header=f"cc_soak_{i}",
            payload=_payload(),
            state=state,
            service=svc,
        )
        if status == 200:
            ok += 1
    assert ok == 100
    snap = metrics.snapshot()
    assert snap["requests_success"] == 100
    assert snap["active_inflight"] == 0
    assert "cobra_core_requests_total" in metrics.render_prometheus()
