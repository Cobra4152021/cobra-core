"""Public API error model — stable across /api/v1."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class ApiErrorCode(StrEnum):
    UNAUTHENTICATED = "unauthenticated"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"
    CONFLICT = "conflict"
    INTERNAL_ERROR = "internal_error"
    VERSION_UNSUPPORTED = "version_unsupported"
    BAD_REQUEST = "bad_request"


DOCUMENTATION_BASE = "https://docs.cobra.local/api/errors"


@dataclass
class ApiError(Exception):
    error_code: ApiErrorCode
    message: str
    request_id: str = ""
    status: int = 400
    details: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def public_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "request_id": self.request_id,
            "timestamp": time.time(),
            "documentation_url": f"{DOCUMENTATION_BASE}/{self.error_code.value}",
            **({"details": self.details} if self.details else {}),
        }


def error_response(
    *,
    error_code: ApiErrorCode | str,
    message: str,
    request_id: str,
    status: int = 400,
    details: dict[str, Any] | None = None,
) -> tuple[int, dict[str, Any]]:
    code = error_code if isinstance(error_code, ApiErrorCode) else ApiErrorCode(error_code)
    body = ApiError(
        error_code=code,
        message=message,
        request_id=request_id,
        status=status,
        details=details,
    ).public_dict()
    return status, body
