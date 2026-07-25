"""Normalized Protocol V1 errors — no tracebacks/paths/env leakage."""

from __future__ import annotations

from typing import Any

# Codes from docs/cobra-protocol/ERROR_CODES.md plus schema-allowed server extensions
# that map into the same normalized object (retryable always false in V1).
KNOWN_CODES = frozenset(
    {
        "auth_failed",
        "bad_request",
        "timeout",
        "provider_error",
        "provider_disabled",
        "missing_base_url",
        "missing_auth_secret",
        "malformed_response",
        "empty_response",
        "cancelled",
        # Server-side distinct limit/unavailability signals (schema: code is string).
        # Frozen ERROR_CODES.md does not list these; HTTP mapping uses 400/502/503.
        "context_limit",
        "output_limit",
        "model_unavailable",
        "unsupported_protocol",
        "incompatible_compatibility",
        "internal_error",
        # RC1 admission / kill-switch (schema allows arbitrary string codes).
        "rate_limited",
    }
)


def normalized_error(
    *,
    code: str,
    message: str,
    request_id: str,
    retryable: bool = False,
) -> dict[str, Any]:
    # Protocol V1: retryable is always false on the wire.
    return {
        "code": code,
        "message": _safe_message(message),
        "retryable": False if retryable is False else False,
        "requestId": request_id,
    }


def _safe_message(message: str) -> str:
    text = (message or "Request failed").strip() or "Request failed"
    # Strip common leakage markers without echoing internals.
    lowered = text.lower()
    banned = ("traceback", 'file "', "file '", "\\\\", "/home/", "/users/", "c:\\", '.py"')
    if any(b in lowered for b in banned):
        return "Request failed"
    return text[:500]


def http_status_for_code(code: str) -> int:
    return {
        "auth_failed": 401,
        "bad_request": 400,
        "unsupported_protocol": 400,
        "incompatible_compatibility": 400,
        "context_limit": 400,
        "output_limit": 400,
        "timeout": 504,
        "cancelled": 499,
        "empty_response": 502,
        "malformed_response": 502,
        "provider_error": 502,
        "model_unavailable": 503,
        "provider_disabled": 503,
        "rate_limited": 429,
        "internal_error": 500,
    }.get(code, 500)
