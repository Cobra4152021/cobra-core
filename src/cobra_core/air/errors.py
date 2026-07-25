"""Typed AIR routing failures (fail closed; never silent vendor swap)."""

from __future__ import annotations

from enum import StrEnum

from cobra_core.cial.errors import CialError, CialErrorCode


class AirRoutingFailureCode(StrEnum):
    """AIR-specific failure reasons (mapped into CIAL taxonomy)."""

    NO_CAPABILITY_MATCH = "no_capability_match"
    NO_HEALTHY_CANDIDATE = "no_healthy_candidate"
    POLICY_EXCLUDED = "policy_excluded"
    LIVE_REQUIRED_UNAVAILABLE = "live_required_unavailable"
    EMPTY_REGISTRY = "empty_registry"


_CIAL_MAP: dict[AirRoutingFailureCode, CialErrorCode] = {
    AirRoutingFailureCode.NO_CAPABILITY_MATCH: CialErrorCode.CAPABILITY_MISMATCH,
    AirRoutingFailureCode.NO_HEALTHY_CANDIDATE: CialErrorCode.PROVIDER_UNAVAILABLE,
    AirRoutingFailureCode.POLICY_EXCLUDED: CialErrorCode.ROUTING_FAILED,
    AirRoutingFailureCode.LIVE_REQUIRED_UNAVAILABLE: CialErrorCode.LIVE_PROVIDER_DISABLED,
    AirRoutingFailureCode.EMPTY_REGISTRY: CialErrorCode.ROUTING_FAILED,
}


class AirRoutingError(CialError):
    """
    Fail-closed AIR decision.

    Raised when no registered model satisfies the request. Never selects an
    alternate model that lacks required capabilities.
    """

    def __init__(self, air_code: AirRoutingFailureCode, message: str) -> None:
        self.air_code = air_code
        super().__init__(_CIAL_MAP[air_code], message)
