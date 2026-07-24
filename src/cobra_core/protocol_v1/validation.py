"""Request validation against Protocol V1 frozen request rules (no schema package mutation)."""

from __future__ import annotations

from typing import Any

from cobra_core.protocol_v1.config import ServerConfig
from cobra_core.protocol_v1.errors import normalized_error


def validate_completion_request(
    payload: dict[str, Any],
    cfg: ServerConfig,
    *,
    request_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """
    Returns (normalized_request, error).
    normalized_request keys: model, stream, max_tokens, messages
    """
    if not isinstance(payload, dict):
        return None, normalized_error(
            code="bad_request",
            message="Request body must be a JSON object",
            request_id=request_id,
        )

    # Governance completion.request.schema.json: stream const false (required).
    if "stream" not in payload:
        return None, normalized_error(
            code="bad_request",
            message="stream is required and must be false",
            request_id=request_id,
        )
    if payload.get("stream") is not False:
        return None, normalized_error(
            code="bad_request",
            message="stream must be false for Protocol V1",
            request_id=request_id,
        )

    model = payload.get("model")
    if not isinstance(model, str) or not model.strip():
        return None, normalized_error(
            code="bad_request",
            message="model is required",
            request_id=request_id,
        )
    model = model.strip()
    if model != cfg.model:
        return None, normalized_error(
            code="bad_request",
            message="unsupported model for this server",
            request_id=request_id,
        )

    if "max_tokens" not in payload:
        return None, normalized_error(
            code="bad_request",
            message="max_tokens is required",
            request_id=request_id,
        )
    try:
        max_tokens = int(payload["max_tokens"])
    except (TypeError, ValueError):
        return None, normalized_error(
            code="bad_request",
            message="max_tokens must be a positive integer",
            request_id=request_id,
        )
    if max_tokens <= 0:
        return None, normalized_error(
            code="bad_request",
            message="max_tokens must be a positive integer",
            request_id=request_id,
        )

    # Frozen fixture behavior: cap to configured output limit (do not silently raise).
    if cfg.max_output_tokens is not None and max_tokens > cfg.max_output_tokens:
        max_tokens = cfg.max_output_tokens

    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        return None, normalized_error(
            code="bad_request",
            message="messages must be a non-empty array",
            request_id=request_id,
        )

    cleaned: list[dict[str, str]] = []
    for m in messages:
        if not isinstance(m, dict):
            return None, normalized_error(
                code="bad_request",
                message="each message must be an object",
                request_id=request_id,
            )
        role = m.get("role")
        content = m.get("content")
        if role not in {"system", "user", "assistant"} or not isinstance(content, str):
            return None, normalized_error(
                code="bad_request",
                message="message role/content invalid",
                request_id=request_id,
            )
        cleaned.append({"role": role, "content": content})

    return {
        "model": model,
        "stream": False,
        "max_tokens": max_tokens,
        "messages": cleaned,
    }, None
