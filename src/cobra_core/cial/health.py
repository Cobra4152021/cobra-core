"""Provider / model health states for CIAL routing eligibility."""

from __future__ import annotations

from enum import StrEnum


class HealthState(StrEnum):
    """Typed health for providers and registered models."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    DISABLED = "disabled"


# Router excludes these from every automatic policy.
EXCLUDED_HEALTH_STATES: frozenset[HealthState] = frozenset(
    {
        HealthState.UNAVAILABLE,
        HealthState.DISABLED,
    }
)

# Eligible for routing (including degraded — see docs/cial/KC019_ROUTING.md).
ELIGIBLE_HEALTH_STATES: frozenset[HealthState] = frozenset(
    {
        HealthState.UNKNOWN,
        HealthState.HEALTHY,
        HealthState.DEGRADED,
    }
)


def is_routable_health(state: HealthState) -> bool:
    """Return True if the model may be selected (not unavailable/disabled)."""
    return state in ELIGIBLE_HEALTH_STATES
