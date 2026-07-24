"""Normalized Protocol V1 errors — no tracebacks/paths/env leakage."""

from __future__ import annotations

from typing import Any


def normalized_error(
    *,
    code: str,
    message: str,
    request_id: str,
    retryable: bool = False,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "retryable": bool(retryable),  # Protocol V1: always false in practice
        "requestId": request_id,
    }


def http_status_for_code(code: str) -> int:
    return {
        "auth_failed": 401,
        "bad_request": 400,
        "timeout": 504,
        "empty_response": 502,
        "malformed_response": 502,
        "provider_error": 502,
        "provider_disabled": 503,
        "cancelled": 499,
    }.get(code, 500)
