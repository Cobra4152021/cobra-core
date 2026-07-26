"""Typed resilience failure taxonomy (fail closed; safe public messages)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class FailureCategory(StrEnum):
    AUTHENTICATION_FAILURE = "authentication_failure"
    AUTHORIZATION_FAILURE = "authorization_failure"
    RATE_LIMITED = "rate_limited"
    PROVIDER_TIMEOUT = "provider_timeout"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    PROVIDER_OVERLOADED = "provider_overloaded"
    CONNECTION_FAILURE = "connection_failure"
    INVALID_PROVIDER_RESPONSE = "invalid_provider_response"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    SCHEMA_REPAIR_FAILED = "schema_repair_failed"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"
    PROVIDER_UNHEALTHY = "provider_unhealthy"
    BUDGET_EXCEEDED = "budget_exceeded"
    REQUEST_DEADLINE_EXCEEDED = "request_deadline_exceeded"
    CIRCUIT_OPEN = "circuit_open"
    OPERATOR_DISABLED = "operator_disabled"
    POLICY_BLOCKED = "policy_blocked"
    INTERNAL_EXECUTION_ERROR = "internal_execution_error"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class FailureTraits:
    retryable: bool
    fallback_eligible: bool
    circuit_breaker_relevant: bool
    operator_action_required: bool
    safe_public_message: str


_TRAITS: dict[FailureCategory, FailureTraits] = {
    FailureCategory.AUTHENTICATION_FAILURE: FailureTraits(
        False, False, False, True, "Provider authentication failed"
    ),
    FailureCategory.AUTHORIZATION_FAILURE: FailureTraits(
        False, False, False, True, "Provider authorization denied"
    ),
    FailureCategory.RATE_LIMITED: FailureTraits(True, True, True, False, "Provider rate limited"),
    FailureCategory.PROVIDER_TIMEOUT: FailureTraits(True, True, True, False, "Provider timed out"),
    FailureCategory.PROVIDER_UNAVAILABLE: FailureTraits(
        True, True, True, False, "Provider unavailable"
    ),
    FailureCategory.PROVIDER_OVERLOADED: FailureTraits(
        True, True, True, False, "Provider overloaded"
    ),
    FailureCategory.CONNECTION_FAILURE: FailureTraits(
        True, True, True, False, "Provider connection failed"
    ),
    FailureCategory.INVALID_PROVIDER_RESPONSE: FailureTraits(
        False, True, False, False, "Invalid provider response"
    ),
    FailureCategory.STRUCTURED_OUTPUT_INVALID: FailureTraits(
        False, False, False, False, "Structured output invalid"
    ),
    FailureCategory.SCHEMA_REPAIR_FAILED: FailureTraits(
        False, False, False, False, "Schema repair failed"
    ),
    FailureCategory.CAPABILITY_UNAVAILABLE: FailureTraits(
        False, False, False, False, "Required capability unavailable"
    ),
    FailureCategory.PROVIDER_UNHEALTHY: FailureTraits(
        False, True, True, False, "Provider unhealthy"
    ),
    FailureCategory.BUDGET_EXCEEDED: FailureTraits(
        False, False, False, True, "Execution budget exceeded"
    ),
    FailureCategory.REQUEST_DEADLINE_EXCEEDED: FailureTraits(
        False, False, False, False, "Request deadline exceeded"
    ),
    FailureCategory.CIRCUIT_OPEN: FailureTraits(
        False, True, False, False, "Provider circuit is open"
    ),
    FailureCategory.OPERATOR_DISABLED: FailureTraits(
        False, False, False, True, "Provider disabled by operator"
    ),
    FailureCategory.POLICY_BLOCKED: FailureTraits(
        False, False, False, False, "Execution blocked by policy"
    ),
    FailureCategory.INTERNAL_EXECUTION_ERROR: FailureTraits(
        False, False, False, True, "Internal execution error"
    ),
    FailureCategory.CANCELLED: FailureTraits(False, False, False, False, "Request cancelled"),
}


def traits_for(category: FailureCategory) -> FailureTraits:
    return _TRAITS[category]


class ResilienceError(Exception):
    """Safe, non-leaking RRF failure."""

    def __init__(
        self,
        category: FailureCategory,
        message: str | None = None,
        *,
        retry_after_ms: int | None = None,
    ) -> None:
        self.category = category
        self.traits = traits_for(category)
        self.message = message or self.traits.safe_public_message
        self.retry_after_ms = retry_after_ms
        super().__init__(self.message)
