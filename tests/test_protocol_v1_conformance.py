"""Protocol V1 server conformance — mock inference, no GPU, governance frozen."""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from cobra_core.protocol_governance.schema_validate import validate_instance
from cobra_core.protocol_governance.verify import compute_hashes, default_protocol_root
from cobra_core.protocol_v1.auth import verify_bearer
from cobra_core.protocol_v1.constants import COMPATIBILITY_VERSION, PROTOCOL_VERSION, PROVIDER_ID
from cobra_core.protocol_v1.handlers import handle_chat_completions, handle_health
from cobra_core.protocol_v1.inference import approx_tokens, truncate_messages
from cobra_core.protocol_v1.inference_service import InferenceService
from cobra_core.protocol_v1.logging_util import sanitize_log_fields
from cobra_core.protocol_v1.request_id import is_valid_request_id, new_request_id
from cobra_core.protocol_v1.runtime_state import RuntimeState
from cobra_core.protocol_v1.streaming import oneshot_stream_error, oneshot_stream_events

REPO = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO / "protocol" / "v1" / "schemas"
FROZEN_SCHEMA_HASH = "f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3"
FROZEN_FIXTURE_HASH = "9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture()
def cfg(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "test-secret-v1")
    monkeypatch.setenv("COBRA_INFERENCE_MODE", "mock")
    monkeypatch.setenv("COBRA_CORE_REVISION", "rev-test")
    monkeypatch.setenv("COBRA_CORE_GIT_SHA", "abc123def456")
    monkeypatch.setenv("COBRA_CORE_MAX_OUTPUT_TOKENS", "64")
    monkeypatch.setenv("COBRA_CORE_MAX_CONTEXT", "100")
    monkeypatch.setenv("COBRA_CORE_TIMEOUT_MS", "3000")
    monkeypatch.setenv("COBRA_CORE_HOST", "127.0.0.1")
    monkeypatch.setenv("COBRA_CORE_PORT", "18765")
    monkeypatch.setenv("COBRA_PROTOCOL_VERSION", "1")
    monkeypatch.setenv("COBRA_COMPATIBILITY_VERSION", "1")
    monkeypatch.setenv("COBRA_INFERENCE_MOCK_DELAY_MS", "0")
    from cobra_core.protocol_v1.config import load_config

    return load_config()


@pytest.fixture()
def runtime(cfg):
    state = RuntimeState(inference_mode=cfg.inference_mode)
    state.mark_loaded()
    service = InferenceService(cfg, state)
    return state, service


def _complete(cfg, runtime, payload, *, auth="Bearer test-secret-v1", rid="cc_t1", cancel=None):
    state, service = runtime
    return handle_chat_completions(
        cfg,
        authorization=auth,
        request_id_header=rid,
        payload=payload,
        state=state,
        service=service,
        cancel_event=cancel,
    )


def test_governance_hashes_unchanged() -> None:
    root = default_protocol_root()
    schema_hash, fixture_hash = compute_hashes(root)
    assert schema_hash == FROZEN_SCHEMA_HASH
    assert fixture_hash == FROZEN_FIXTURE_HASH


def test_auth_constant_time_match() -> None:
    assert verify_bearer("Bearer secret", "secret") is True
    assert verify_bearer("Bearer wrong", "secret") is False
    assert verify_bearer(None, "secret") is False
    assert verify_bearer("Bearer ", "secret") is False
    assert verify_bearer("Basic secret", "secret") is False
    assert verify_bearer("Bearer secret", "") is False


def test_health_schema(cfg, runtime) -> None:
    state, service = runtime
    gens_before = state.generation_calls
    st, body, rid = handle_health(
        cfg,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_h1",
        state=state,
        service=service,
    )
    assert st == 200
    assert rid == "cc_h1"
    assert state.generation_calls == gens_before  # health performs no generation
    validate_instance(body, _load_schema("health.response.schema.json"), base_dir=SCHEMA_DIR)


def test_health_auth_variants(cfg, runtime) -> None:
    state, service = runtime
    for auth in (None, "Bearer", "Bearer ", "Bearer nope", "Token x"):
        st, body, _ = handle_health(
            cfg, authorization=auth, request_id_header=None, state=state, service=service
        )
        assert st == 401
        assert body["code"] == "auth_failed"
        assert body["retryable"] is False
        validate_instance(body, _load_schema("error.schema.json"), base_dir=SCHEMA_DIR)


def test_completion_request_and_response_schema(cfg, runtime) -> None:
    payload = {
        "model": "cobra-core-qwen3-8b",
        "stream": False,
        "max_tokens": 32,
        "messages": [{"role": "user", "content": "hello"}],
    }
    validate_instance(payload, _load_schema("completion.request.schema.json"), base_dir=SCHEMA_DIR)
    st, body, rid = _complete(cfg, runtime, payload, rid="cc_c1")
    assert st == 200
    assert rid == "cc_c1"
    validate_instance(body, _load_schema("completion.response.schema.json"), base_dir=SCHEMA_DIR)


def test_stream_event_schema_from_oneshot(cfg, runtime) -> None:
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "x"}],
        },
        rid="cc_stream",
    )
    assert st == 200
    text = body["choices"][0]["message"]["content"]
    events = oneshot_stream_events(text=text, request_id="cc_stream")
    validate_instance(events, _load_schema("streaming.events.schema.json"), base_dir=SCHEMA_DIR)


def test_stream_true_rejected(cfg, runtime) -> None:
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": True,
            "max_tokens": 16,
            "messages": [{"role": "user", "content": "x"}],
        },
    )
    assert st == 400
    assert body["code"] == "bad_request"


def test_request_id_preservation_and_generation(cfg, runtime) -> None:
    st, body, rid = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "id"}],
        },
        rid="cc_preserve",
    )
    assert rid == "cc_preserve" and body["requestId"] == "cc_preserve"
    st, body, rid = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "id"}],
        },
        rid=None,
    )
    assert st == 200 and rid.startswith("cc_") and is_valid_request_id(rid)
    assert new_request_id("bad id with spaces").startswith("cc_")


def test_invalid_json_path_via_server(cfg, monkeypatch: pytest.MonkeyPatch) -> None:
    from cobra_core.protocol_v1.server import make_server

    httpd = make_server(cfg)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    base = f"http://{cfg.host}:{cfg.port}"
    try:
        r = urllib.request.Request(
            f"{base}/v1/chat/completions",
            data=b"{not-json",
            headers={
                "Authorization": "Bearer test-secret-v1",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as ei:
            urllib.request.urlopen(r, timeout=5)
        assert ei.value.code == 400
        payload = json.loads(ei.value.read().decode())
        assert payload["code"] == "bad_request"
        assert "traceback" not in json.dumps(payload).lower()
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_invalid_messages_and_unsupported_model(cfg, runtime) -> None:
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [],
        },
    )
    assert st == 400 and body["code"] == "bad_request"
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "other-model",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "x"}],
        },
    )
    assert st == 400 and body["code"] == "bad_request"


def test_context_and_output_limits(cfg, runtime, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_MAX_CONTEXT", "5")
    from cobra_core.protocol_v1.config import load_config

    tight = load_config()
    state = RuntimeState(inference_mode="mock")
    state.mark_loaded()
    service = InferenceService(tight, state)
    # Newest alone exceeds context -> distinct context_limit
    st, body, rid = handle_chat_completions(
        tight,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_ctx",
        payload={
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "x" * 200}],
        },
        state=state,
        service=service,
    )
    assert st == 400 and body["code"] == "context_limit" and rid == "cc_ctx"

    # Output capped (fixture behavior) — success with shortened mock text
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 10_000,
            "messages": [{"role": "user", "content": "limit-me-" + ("y" * 200)}],
        },
    )
    assert st == 200
    assert len(body["choices"][0]["message"]["content"]) <= 64 * 4


def test_usage_and_latency(cfg, runtime) -> None:
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 32,
            "messages": [{"role": "user", "content": "hello"}],
        },
    )
    assert st == 200
    u = body["usage"]
    assert u["total_tokens"] == u["prompt_tokens"] + u["completion_tokens"]
    validate_instance(u, _load_schema("usage.schema.json"), base_dir=SCHEMA_DIR)
    lat = body["latency"]
    assert all(lat[k] >= 0 for k in ("queue_ms", "provider_latency_ms", "inference_ms", "total_ms"))
    validate_instance(lat, _load_schema("latency.schema.json"), base_dir=SCHEMA_DIR)


def test_timeout(cfg, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_TIMEOUT_MS", "50")
    monkeypatch.setenv("COBRA_INFERENCE_MOCK_DELAY_MS", "500")
    from cobra_core.protocol_v1.config import load_config

    slow = load_config()
    state = RuntimeState(inference_mode="mock")
    state.mark_loaded()
    service = InferenceService(slow, state)
    st, body, rid = handle_chat_completions(
        slow,
        authorization="Bearer test-secret-v1",
        request_id_header="cc_to",
        payload={
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "slow"}],
        },
        state=state,
        service=service,
    )
    assert st == 504 and body["code"] == "timeout" and rid == "cc_to"
    validate_instance(
        {k: body[k] for k in ("code", "message", "retryable", "requestId")},
        _load_schema("error.schema.json"),
        base_dir=SCHEMA_DIR,
    )


def test_cancellation(cfg, runtime) -> None:
    cancel = threading.Event()
    cancel.set()
    st, body, rid = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "x"}],
        },
        rid="cc_cancel",
        cancel=cancel,
    )
    assert st == 499 and body["code"] == "cancelled" and rid == "cc_cancel"


def test_inference_failure_sanitized(cfg, runtime) -> None:
    state, service = runtime
    service._force_fail = True  # noqa: SLF001
    st, body, _ = _complete(
        cfg,
        runtime,
        {
            "model": "cobra-core-qwen3-8b",
            "stream": False,
            "max_tokens": 8,
            "messages": [{"role": "user", "content": "x"}],
        },
    )
    assert st == 502 and body["code"] == "provider_error"
    blob = json.dumps(body).lower()
    assert "traceback" not in blob
    assert "test-secret" not in blob
    assert "\\" not in body["message"]


def test_no_secret_in_logs(cfg, runtime, caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.INFO, logger="cobra_core.protocol_v1"):
        handle_health(
            cfg,
            authorization="Bearer test-secret-v1",
            request_id_header="cc_log",
            state=runtime[0],
            service=runtime[1],
        )
        _complete(
            cfg,
            runtime,
            {
                "model": "cobra-core-qwen3-8b",
                "stream": False,
                "max_tokens": 8,
                "messages": [{"role": "user", "content": "secret-prompt-should-not-log"}],
            },
        )
    text = "\n".join(r.message for r in caplog.records)
    assert "test-secret-v1" not in text
    assert "secret-prompt-should-not-log" not in text
    assert "Authorization" not in text


def test_redaction_strips_forbidden_fields() -> None:
    safe = sanitize_log_fields(
        {
            "requestId": "cc_1",
            "authorization": "Bearer secret",
            "prompt": "hello",
            "status": 200,
        }
    )
    assert "authorization" not in safe
    assert "prompt" not in safe
    assert safe["status"] == 200


def test_oneshot_stream_error_schema() -> None:
    err = {
        "code": "provider_error",
        "message": "Inference failed",
        "retryable": False,
        "requestId": "cc_e",
    }
    events = oneshot_stream_error(request_id="cc_e", error=err)
    validate_instance(events, _load_schema("streaming.events.schema.json"), base_dir=SCHEMA_DIR)


def test_truncate_messages_keeps_newest() -> None:
    msgs = [{"role": "user", "content": "a" * 200}, {"role": "user", "content": "short"}]
    out, err = truncate_messages(msgs, max_context=10)
    assert err is None
    assert out[-1]["content"] == "short"


def test_approx_tokens() -> None:
    assert approx_tokens("") == 0
    assert approx_tokens("abcd") == 1


def test_cobrabench_not_imported() -> None:
    import sys

    assert not any("cobrabench_run" in m for m in sys.modules)


def test_http_server_valid_auth(cfg) -> None:
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
            assert body["protocolVersion"] == PROTOCOL_VERSION
            assert body["compatibilityVersion"] == COMPATIBILITY_VERSION
            assert body["providerId"] == PROVIDER_ID
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_non_loopback_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "x")
    monkeypatch.setenv("COBRA_CORE_HOST", "0.0.0.0")
    from cobra_core.protocol_v1.config import load_config
    from cobra_core.protocol_v1.server import make_server

    with pytest.raises(RuntimeError, match="loopback"):
        make_server(load_config())


def test_unsupported_protocol_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("COBRA_CORE_AUTH_SECRET", "x")
    monkeypatch.setenv("COBRA_PROTOCOL_VERSION", "2")
    from cobra_core.protocol_v1.config import ConfigError, load_config

    with pytest.raises(ConfigError, match="PROTOCOL_VERSION"):
        load_config()
