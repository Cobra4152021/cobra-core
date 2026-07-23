"""Unsupported-claim evaluators (v1 preserved, v2 classify-then-support)."""

from cobra_core.evaluators.unsupported_claims.types import (
    ClaimClass,
    ClaimSpanResult,
    SupportState,
    UnsupportedClaimEvaluation,
)
from cobra_core.evaluators.unsupported_claims.v1 import evaluate_unsupported_claims_v1
from cobra_core.evaluators.unsupported_claims.v2 import evaluate_unsupported_claims_v2

__all__ = [
    "ClaimClass",
    "ClaimSpanResult",
    "SupportState",
    "UnsupportedClaimEvaluation",
    "evaluate_unsupported_claims_v1",
    "evaluate_unsupported_claims_v2",
]
