"""Request validation helpers for the public API."""

from __future__ import annotations

from typing import Any

from cobra_core.api.errors import ApiError, ApiErrorCode


def require_str(payload: dict[str, Any], key: str, *, max_len: int = 200) -> str:
    val = payload.get(key)
    if not isinstance(val, str) or not val.strip():
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message=f"{key} is required",
            status=400,
        )
    s = val.strip()
    if len(s) > max_len:
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message=f"{key} exceeds max length {max_len}",
            status=400,
        )
    return s


def optional_str(payload: dict[str, Any], key: str, *, default: str = "") -> str:
    val = payload.get(key, default)
    if val is None:
        return default
    if not isinstance(val, str):
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message=f"{key} must be a string",
            status=400,
        )
    return val.strip()


def require_object(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise ApiError(
            error_code=ApiErrorCode.VALIDATION_ERROR,
            message="JSON object body required",
            status=400,
        )
    return payload
