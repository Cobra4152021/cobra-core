"""Protocol V1 request handlers (transport-facing orchestration only)."""

from __future__ import annotations

import json
import threading
from typing import Any

from cobra_core.protocol_v1.auth import verify_bearer
from cobra_core.protocol_v1.config import ServerConfig
from cobra_core.protocol_v1.constants import (
    CAPABILITY_KEYS,
    COMPATIBILITY_VERSION,
    PROTOCOL_VERSION,
    PROVIDER_ID,
)
from cobra_core.protocol_v1.errors import http_status_for_code, normalized_error
from cobra_core.protocol_v1.inference_service import InferenceService
from cobra_core.protocol_v1.logging_util import log_event
from cobra_core.protocol_v1.request_id import new_request_id
from cobra_core.protocol_v1.runtime_state import RuntimeState
from cobra_core.protocol_v1.timing import Stopwatch, latency_block
from cobra_core.protocol_v1.validation import validate_completion_request


def capabilities() -> dict[str, bool]:
    # streaming=true => Computer-compatible one-shot-backed streaming (not native SSE).
    caps = {
        "streaming": True,
        "vision": False,
        "toolCalling": False,
        "jsonMode": False,
        "thinking": False,
        "embeddings": False,
    }
    assert set(caps) == set(CAPABILITY_KEYS)
    return caps


def identity(cfg: ServerConfig) -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "compatibilityVersion": COMPATIBILITY_VERSION,
        "providerId": PROVIDER_ID,
        "model": cfg.model,
        "revision": cfg.revision,
        "gitSha": cfg.git_sha,
        "capabilities": capabilities(),
    }


def limits(cfg: ServerConfig) -> dict[str, Any]:
    return {
        "maxContext": cfg.max_context,
        "maxOutputTokens": cfg.max_output_tokens,
        "timeoutMs": cfg.timeout_ms,
    }


def handle_health(
    cfg: ServerConfig,
    *,
    authorization: str | None,
    request_id_header: str | None,
    state: RuntimeState | None = None,
    service: InferenceService | None = None,
) -> tuple[int, dict[str, Any], str]:
    """
    Health must never execute generation.

    `service` is accepted for dependency injection but must not call complete().
    """
    del service  # explicit: health path never uses inference.complete
    sw = Stopwatch.start()
    request_id = new_request_id(request_id_header)
    rt = state or RuntimeState(inference_mode=cfg.inference_mode)

    if not cfg.auth_configured:
        err = normalized_error(
            code="auth_failed",
            message="Server auth secret is not configured",
            request_id=request_id,
        )
        log_event(
            "health",
            status=401,
            code="auth_failed",
            requestId=request_id,
            endpoint="/health",
        )
        return http_status_for_code("auth_failed"), err, request_id
    if not verify_bearer(authorization, cfg.auth_secret):
        err = normalized_error(
            code="auth_failed",
            message="Cobra Core authentication failed",
            request_id=request_id,
        )
        log_event(
            "health",
            status=401,
            code="auth_failed",
            requestId=request_id,
            endpoint="/health",
        )
        return http_status_for_code("auth_failed"), err, request_id

    reason = rt.health_reason()
    ready = rt.inference_ready
    total = sw.ms_since()
    body = {
        **identity(cfg),
        "provider": PROVIDER_ID,
        "enabled": True,
        "authenticated": True,
        "reachable": True,
        "reason": reason if ready else reason,
        "limits": limits(cfg),
        "requestId": request_id,
        "latency": latency_block(
            queue_ms=0,
            provider_latency_ms=total,
            inference_ms=0,
            total_ms=total,
        ),
    }
    log_event(
        "health",
        status=200,
        requestId=request_id,
        endpoint="/health",
        protocolVersion=PROTOCOL_VERSION,
        compatibilityVersion=COMPATIBILITY_VERSION,
        model=cfg.model,
        revision=cfg.revision,
        reason=reason,
        latency_ms=total,
    )
    return 200, body, request_id


def handle_chat_completions(
    cfg: ServerConfig,
    *,
    authorization: str | None,
    request_id_header: str | None,
    payload: dict[str, Any],
    state: RuntimeState | None = None,
    service: InferenceService | None = None,
    cancel_event: threading.Event | None = None,
) -> tuple[int, dict[str, Any], str]:
    sw = Stopwatch.start()
    request_id = new_request_id(request_id_header)
    rt = state or RuntimeState(inference_mode=cfg.inference_mode)
    svc = service or InferenceService(cfg, rt)
    cancel = cancel_event or threading.Event()

    if not cfg.auth_configured or not verify_bearer(authorization, cfg.auth_secret):
        err = normalized_error(
            code="auth_failed",
            message="Cobra Core authentication failed",
            request_id=request_id,
        )
        log_event(
            "completion",
            status=401,
            code="auth_failed",
            requestId=request_id,
            endpoint="/v1/chat/completions",
        )
        return http_status_for_code("auth_failed"), err, request_id

    normalized, err = validate_completion_request(payload, cfg, request_id=request_id)
    if err is not None or normalized is None:
        assert err is not None
        log_event(
            "completion",
            status=400,
            code=err.get("code"),
            requestId=request_id,
            endpoint="/v1/chat/completions",
        )
        return 400, err, request_id

    if not rt.inference_ready and cfg.inference_mode not in {"mock", "echo", "test"}:
        # Attempt lazy load once; failures become model_unavailable.
        try:
            svc.ensure_runtime()
        except Exception:
            e = normalized_error(
                code="model_unavailable",
                message="Model runtime is unavailable",
                request_id=request_id,
            )
            log_event(
                "completion",
                status=503,
                code="model_unavailable",
                requestId=request_id,
                endpoint="/v1/chat/completions",
            )
            return 503, e, request_id

    outcome = svc.complete(
        normalized["messages"],
        int(normalized["max_tokens"]),
        cancel_event=cancel,
        timeout_ms=cfg.timeout_ms,
    )
    total = sw.ms_since()

    if not outcome.ok:
        code = outcome.error_code or "provider_error"
        status = http_status_for_code(code)
        err_body = normalized_error(
            code=code,
            message=outcome.error_message or "Request failed",
            request_id=request_id,
        )
        # Frozen error.schema.json sets additionalProperties:false — do not attach latency.
        log_event(
            "completion",
            status=status,
            code=code,
            requestId=request_id,
            endpoint="/v1/chat/completions",
            model=cfg.model,
            latency_ms=total,
        )
        return status, err_body, request_id

    assert outcome.result is not None
    inf = outcome.result
    if not (inf.content or "").strip():
        err_body = normalized_error(
            code="empty_response",
            message="Cobra Core returned an empty completion",
            request_id=request_id,
        )
        return http_status_for_code("empty_response"), err_body, request_id

    # If client cancelled after inference finished, do not deliver success.
    if cancel.is_set():
        err_body = normalized_error(
            code="cancelled",
            message="Request cancelled",
            request_id=request_id,
        )
        return http_status_for_code("cancelled"), err_body, request_id

    body = {
        "id": request_id,
        "object": "chat.completion",
        "model": normalized["model"],
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": inf.content},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": inf.prompt_tokens,
            "completion_tokens": inf.completion_tokens,
            "total_tokens": inf.prompt_tokens + inf.completion_tokens,
        },
        "latency": latency_block(
            queue_ms=outcome.queue_ms,
            provider_latency_ms=outcome.provider_latency_ms or total,
            inference_ms=inf.inference_ms,
            total_ms=total,
        ),
        "protocolVersion": PROTOCOL_VERSION,
        "compatibilityVersion": COMPATIBILITY_VERSION,
        "requestId": request_id,
        **{k: identity(cfg)[k] for k in ("providerId", "revision", "gitSha", "capabilities")},
    }
    log_event(
        "completion",
        status=200,
        requestId=request_id,
        endpoint="/v1/chat/completions",
        protocolVersion=PROTOCOL_VERSION,
        compatibilityVersion=COMPATIBILITY_VERSION,
        model=cfg.model,
        revision=cfg.revision,
        prompt_tokens=inf.prompt_tokens,
        completion_tokens=inf.completion_tokens,
        total_tokens=inf.prompt_tokens + inf.completion_tokens,
        latency_ms=total,
    )
    return 200, body, request_id


def dumps(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
