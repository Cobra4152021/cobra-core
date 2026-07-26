"""Map provider/transport exceptions into typed failure categories."""

from __future__ import annotations

from cobra_core.resilience.errors import FailureCategory, ResilienceError


def classify_exception(exc: BaseException) -> ResilienceError:
    if isinstance(exc, ResilienceError):
        return exc
    try:
        from cobra_core.protocol_v1.inference import InferenceCancelledError

        if isinstance(exc, InferenceCancelledError):
            return ResilienceError(FailureCategory.CANCELLED)
    except Exception:  # noqa: BLE001
        pass
    try:
        from cobra_core.cial.errors import CialError, CialErrorCode

        if isinstance(exc, CialError):
            mapping = {
                CialErrorCode.AUTHENTICATION_FAILED: FailureCategory.AUTHENTICATION_FAILURE,
                CialErrorCode.RATE_LIMITED: FailureCategory.RATE_LIMITED,
                CialErrorCode.TIMEOUT: FailureCategory.PROVIDER_TIMEOUT,
                CialErrorCode.PROVIDER_UNAVAILABLE: FailureCategory.PROVIDER_UNAVAILABLE,
                CialErrorCode.QUOTA_EXCEEDED: FailureCategory.BUDGET_EXCEEDED,
                CialErrorCode.LIVE_PROVIDER_DISABLED: FailureCategory.OPERATOR_DISABLED,
                CialErrorCode.INVALID_RESPONSE: FailureCategory.INVALID_PROVIDER_RESPONSE,
                CialErrorCode.CAPABILITY_MISMATCH: FailureCategory.CAPABILITY_UNAVAILABLE,
            }
            cat = mapping.get(exc.code, FailureCategory.PROVIDER_UNAVAILABLE)
            return ResilienceError(cat, (exc.message or "")[:160] or None)
    except Exception:  # noqa: BLE001
        pass

    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "timeout" in name or "timeout" in msg:
        return ResilienceError(FailureCategory.PROVIDER_TIMEOUT)
    if "connection" in name or "connection" in msg or "reset" in msg:
        return ResilienceError(FailureCategory.CONNECTION_FAILURE)
    if "429" in msg or "rate limit" in msg:
        retry_after = None
        if hasattr(exc, "retry_after_ms"):
            try:
                retry_after = int(exc.retry_after_ms)
            except (TypeError, ValueError):
                retry_after = None
        return ResilienceError(FailureCategory.RATE_LIMITED, retry_after_ms=retry_after)
    if "401" in msg:
        return ResilienceError(FailureCategory.AUTHENTICATION_FAILURE)
    if "403" in msg:
        return ResilienceError(FailureCategory.AUTHORIZATION_FAILURE)
    if "503" in msg:
        return ResilienceError(FailureCategory.PROVIDER_UNAVAILABLE)
    if "502" in msg or "500" in msg:
        return ResilienceError(FailureCategory.PROVIDER_OVERLOADED)
    if "cancel" in name or "cancel" in msg:
        return ResilienceError(FailureCategory.CANCELLED)
    return ResilienceError(FailureCategory.INTERNAL_EXECUTION_ERROR, str(exc)[:160])
