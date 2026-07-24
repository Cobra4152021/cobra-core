"""Request handlers for Protocol V1 endpoints."""

from __future__ import annotations

import json
import uuid
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
from cobra_core.protocol_v1.inference import run_inference, truncate_messages
from cobra_core.protocol_v1.timing import Stopwatch, latency_block


def new_request_id(incoming: str | None) -> str:
    raw = (incoming or "").strip()
    if raw:
        return raw
    return f"cc_{uuid.uuid4()}"


def capabilities() -> dict[str, bool]:
    # streaming=true means Computer-compatible one-shot-backed streaming (not native SSE).
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
) -> tuple[int, dict[str, Any], str]:
    sw = Stopwatch.start()
    request_id = new_request_id(request_id_header)
    if not cfg.auth_configured:
        err = normalized_error(
            code="auth_failed",
            message="Server auth secret is not configured",
            request_id=request_id,
        )
        return http_status_for_code("auth_failed"), err, request_id
    if not verify_bearer(authorization, cfg.auth_secret):
        err = normalized_error(
            code="auth_failed",
            message="Cobra Core authentication failed",
            request_id=request_id,
        )
        return http_status_for_code("auth_failed"), err, request_id

    total = sw.ms_since()
    body = {
        **identity(cfg),
        "provider": PROVIDER_ID,
        "enabled": True,
        "authenticated": True,
        "reachable": True,
        "reason": "ok",
        "limits": limits(cfg),
        "requestId": request_id,
        "latency": latency_block(
            queue_ms=0,
            provider_latency_ms=total,
            inference_ms=0,
            total_ms=total,
        ),
    }
    return 200, body, request_id


def _cap_max_tokens(cfg: ServerConfig, requested: Any) -> int | dict[str, Any]:
    try:
        n = int(requested)
    except (TypeError, ValueError):
        n = 2048
    if n <= 0:
        return normalized_error(
            code="bad_request",
            message="max_tokens must be a positive integer",
            request_id="",  # filled by caller
        )
    if cfg.max_output_tokens is not None:
        n = min(n, cfg.max_output_tokens)
    return n


def handle_chat_completions(
    cfg: ServerConfig,
    *,
    authorization: str | None,
    request_id_header: str | None,
    payload: dict[str, Any],
) -> tuple[int, dict[str, Any], str]:
    sw = Stopwatch.start()
    request_id = new_request_id(request_id_header)

    if not cfg.auth_configured or not verify_bearer(authorization, cfg.auth_secret):
        err = normalized_error(
            code="auth_failed",
            message="Cobra Core authentication failed",
            request_id=request_id,
        )
        return http_status_for_code("auth_failed"), err, request_id

    if not isinstance(payload, dict):
        err = normalized_error(
            code="bad_request",
            message="Request body must be a JSON object",
            request_id=request_id,
        )
        return 400, err, request_id

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        err = normalized_error(
            code="bad_request",
            message="messages must be a non-empty array",
            request_id=request_id,
        )
        return 400, err, request_id

    cleaned: list[dict[str, Any]] = []
    for m in messages:
        if not isinstance(m, dict):
            err = normalized_error(
                code="bad_request",
                message="each message must be an object",
                request_id=request_id,
            )
            return 400, err, request_id
        role = m.get("role")
        content = m.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str):
            err = normalized_error(
                code="bad_request",
                message="message role/content invalid",
                request_id=request_id,
            )
            return 400, err, request_id
        cleaned.append({"role": role, "content": content})

    max_tokens = _cap_max_tokens(cfg, payload.get("max_tokens", 2048))
    if isinstance(max_tokens, dict):
        max_tokens["requestId"] = request_id
        return 400, max_tokens, request_id

    model = str(payload.get("model") or cfg.model).strip() or cfg.model
    # stream flag ignored — Protocol V1 one-shot only (see STREAMING.md).
    cleaned = truncate_messages(cleaned, cfg.max_context)

    # Soft timeout: if mock/inference exceeds configured budget, return timeout.
    # (Mock is fast; this guards future backends.)
    inf = run_inference(mode=cfg.inference_mode, messages=cleaned, max_tokens=int(max_tokens))
    elapsed = sw.ms_since()
    if elapsed > cfg.timeout_ms:
        err = normalized_error(
            code="timeout",
            message="Cobra Core request timed out",
            request_id=request_id,
        )
        return 504, err, request_id

    if not (inf.content or "").strip():
        err = normalized_error(
            code="empty_response",
            message="Cobra Core returned an empty completion",
            request_id=request_id,
        )
        return http_status_for_code("empty_response"), err, request_id

    total = sw.ms_since()
    inference_ms = inf.inference_ms if inf.inference_ms > 0 else total
    body = {
        "id": request_id,
        "object": "chat.completion",
        "model": model,
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
            queue_ms=0,
            provider_latency_ms=total,
            inference_ms=inference_ms,
            total_ms=total,
        ),
        "protocolVersion": PROTOCOL_VERSION,
        "compatibilityVersion": COMPATIBILITY_VERSION,
        "requestId": request_id,
        **{k: identity(cfg)[k] for k in ("providerId", "revision", "gitSha", "capabilities")},
    }
    return 200, body, request_id


def dumps(obj: dict[str, Any]) -> bytes:
    return (json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8")
