"""Protocol V1 conformance tests — mock inference, no GPU."""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from cobra_core.protocol_v1.auth import verify_bearer
from cobra_core.protocol_v1.constants import COMPATIBILITY_VERSION, PROTOCOL_VERSION, PROVIDER_ID
from cobra_core.protocol_v1.handlers import handle_chat_completions, handle_health
from cobra_core.protocol_v1.inference import approx_tokens, truncate_messages


@pytest.fixture()
def cfg(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "test-secret-v1")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    monkeypatch.setenv("COBRA_CORE_REVISION", "rev-test")
    monkeypatch.setenv("COBRA_CORE_GIT_SHA", "abc123def456")
    monkeypatch.setenv("COBRA_CORE_MAX_OUTPUT_TOKENS", "64")
    monkeypatch.setenv("COBRA_CORE_MAX_CONTEXT", "100")
    monkeypatch.setenv("COBRA_CORE_TIMEOUT_MS", "3000")
    monkeypatch.setenv("COBRA_PROTOCOL_HOST", "127.0.0.1")
    monkeypatch.setenv("COBRA_PROTOCOL_PORT", "18765")
    from cobra_core.protocol_v1.config import load_config

    return load_config()


def test_auth_constant_time_match() -> None:
    assert verify_bearer("Bearer secret", "secret") is True
    assert verify_bearer("Bearer wrong", "secret") is False
    assert verify_bearer(None, "secret") is False
    assert verify_bearer("Bearer secret", "") is False


def test_health_identity(cfg) -> None:
    st, body, rid = handle_health(
        cfg, authorization="Bearer test-secret-v1", request_id_header="cc_h1"
    )
    assert st == 200
    assert rid == "cc_h1"
    assert body["protocolVersion"] == PROTOCOL_VERSION
    assert body["compatibilityVersion"] == COMPATIBILITY_VERSION
    assert body["providerId"] == PROVIDER_ID
    assert body["provider"] == PROVIDER_ID
    assert body["reason"] == "ok"
    assert body["capabilities"]["streaming"] is True
    assert body["capabilities"]["vision"] is False
    assert "limits" in body
    assert body["revision"] == "rev-test"
    assert body["gitSha"] == "abc123def456"


def test_health_auth_failed(cfg) -> None:
    st, body, _ = handle_health(cfg, authorization="Bearer nope", request_id_header=None)
    assert st == 401
    assert body["code"] == "auth_failed"
    assert body["retryable"] is False
    assert "requestId" in body


def test_completion_contract(cfg) -> None:
    st, body, rid = handle_chat_completions(
        cfg,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_c1",
        payload={
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 32,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert st == 200
    assert rid == "cc_c1"
    assert body["choices"][0]["message"]["content"]
    assert body["usage"]["total_tokens"] >= body["usage"]["prompt_tokens"]
    assert set(body["latency"]) == {
        "queue_ms",
        "provider_latency_ms",
        "inference_ms",
        "total_ms",
    }
    assert body["protocolVersion"] == "1"
    assert body["compatibilityVersion"] == "1"


def test_stream_true_still_oneshot(cfg) -> None:
    st, body, _ = handle_chat_completions(
        cfg,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_c2",
        payload={
            "model": "cobra-core-qwen3-8b",
            "stream": True,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "x"}],
        },
    )
    assert st == 200
    assert "choices" in body  # JSON completion, not SSE


def test_output_limit(cfg) -> None:
    st, body, _ = handle_chat_completions(
        cfg,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_lim",
        payload={
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 10_000,
            "messages": [{"role": "user", "content": "limit-me-" + ("y" * 200)}],
        },
    )
    assert st == 200
    content = body["choices"][0]["message"]["content"]
    # capped to 64 tokens => ~256 chars max in mock
    assert len(content) <= 64 * 4


def test_bad_messages(cfg) -> None:
    st, body, _ = handle_chat_completions(
        cfg,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_bad",
        payload={"model": "x", "stream": False, "max_tokens": 8, "messages": []},
    )
    assert st == 400
    assert body["code"] == "bad_request"


def test_truncate_messages_keeps_newest() -> None:
    msgs = [{"role": "user", "content": "a" * 200}, {"role": "user", "content": "short"}]
    out = truncate_messages(msgs, max_context=10)
    assert out[-1]["content"] == "short"


def test_approx_tokens() -> None:
    assert approx_tokens("") == 0
    assert approx_tokens("abcd") == 1


def test_http_server_loopback(cfg, monkeypatch: pytest.MonkeyPatch) -> None:
    from cobra_core.protocol_v1.server import make_server

    httpd = make_server(cfg)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    base = f"http://{cfg.host}:{cfg.port}"
    try:
        r = urllib.request.Request(
            f"{base}/health",
            headers={"Authorization": "Bearer test-secret-v1", "Accept": "application/json"},
        )
        with urllib.request.urlopen(r, timeout=5) as resp:
            body = json.loads(resp.read().decode())
            assert resp.headers.get("x-request-id")
            assert body["reason"] == "ok"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_non_loopback_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "x")
    monkeypatch.setenv("COBRA_PROTOCOL_HOST", "0.0.0.0")
    from cobra_core.protocol_v1.config import load_config
    from cobra_core.protocol_v1.server import make_server

    with pytest.raises(RuntimeError, match="loopback"):
        make_server(load_config())
