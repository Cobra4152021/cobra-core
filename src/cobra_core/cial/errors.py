"""Stable CIAL error taxonomy mapped into Protocol V1 wire codes."""

from __future__ import annotations

from enum import StrEnum

from cobra_core.protocol_v1.inference import InferenceFailedError


class CialErrorCode(StrEnum):
    """Internal CIAL error codes (not Protocol V1 wire codes)."""

    PROVIDER_NOT_FOUND = "provider_not_found"
    MODEL_NOT_FOUND = "model_not_found"
    MODEL_DISABLED = "model_disabled"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    CAPABILITY_MISMATCH = "capability_mismatch"
    ROUTING_FAILED = "routing_failed"
    AUTHENTICATION_FAILED = "authentication_failed"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"
    INVALID_RESPONSE = "invalid_response"
    INFERENCE_FAILED = "inference_failed"


# Map CIAL taxonomy → existing Protocol V1 ServiceOutcome / wire codes.
_PROTOCOL_CODE_MAP: dict[CialErrorCode, str] = {
    CialErrorCode.PROVIDER_NOT_FOUND: "model_unavailable",
    CialErrorCode.MODEL_NOT_FOUND: "model_unavailable",
    CialErrorCode.MODEL_DISABLED: "provider_disabled",
    CialErrorCode.PROVIDER_UNAVAILABLE: "model_unavailable",
    CialErrorCode.CAPABILITY_MISMATCH: "bad_request",
    CialErrorCode.ROUTING_FAILED: "model_unavailable",
    CialErrorCode.AUTHENTICATION_FAILED: "auth_failed",
    CialErrorCode.RATE_LIMITED: "rate_limited",
    CialErrorCode.TIMEOUT: "timeout",
    CialErrorCode.INVALID_RESPONSE: "malformed_response",
    CialErrorCode.INFERENCE_FAILED: "provider_error",
}


class CialError(Exception):
    """Safe, non-leaking CIAL failure."""

    def __init__(self, code: CialErrorCode | str, message: str) -> None:
        if isinstance(code, CialErrorCode):
            self.code = code
        else:
            self.code = CialErrorCode(code)
        self.message = message
        super().__init__(message)

    @property
    def protocol_code(self) -> str:
        return to_protocol_code(self.code)


def to_protocol_code(code: CialErrorCode | str) -> str:
    """Translate a CIAL code into a Protocol V1 error code string."""
    if isinstance(code, str):
        try:
            code = CialErrorCode(code)
        except ValueError:
            return "provider_error"
    return _PROTOCOL_CODE_MAP.get(code, "provider_error")


def to_inference_failed(exc: CialError) -> InferenceFailedError:
    """Bridge CIAL errors into the Protocol V1 inference failure type."""
    return InferenceFailedError(exc.protocol_code, exc.message)
