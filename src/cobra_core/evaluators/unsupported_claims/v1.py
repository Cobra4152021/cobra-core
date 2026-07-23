"""Unsupported-claim evaluator v1 — preserved CobraBench v0.1 heuristic."""

from __future__ import annotations

from typing import Any

from cobra_core.evaluation.citations import citation_metrics
from cobra_core.evaluators.unsupported_claims.types import UnsupportedClaimEvaluation

EVALUATOR_VERSION = "1.0.0"
IMPLEMENTATION = "cobrabench-citation-heuristic-v0.1"


def evaluate_unsupported_claims_v1(
    response: str,
    allowed_keys: list[str],
    supporting_source_texts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Run the original v1 heuristic via citation_metrics.

    Preserved for official CobraBench v0.1 compatibility. Do not modify behavior.
    """
    metrics = citation_metrics(response, allowed_keys, supporting_source_texts)
    return {
        "evaluator_name": "unsupported_claims",
        "evaluator_version": EVALUATOR_VERSION,
        "implementation": IMPLEMENTATION,
        "unsupported_claim_count": metrics["unsupported_claim_count"],
        "citation_metrics": metrics,
        "deprecated_for_model_quality": True,
        "notes": (
            "v1 treats many uncited sentences as unsupported. "
            "Phase 2E audit found ~0% precision on a 50-flag sample."
        ),
    }


def summarize_v1_as_evaluation(
    response: str,
    allowed_keys: list[str],
    supporting_source_texts: dict[str, str] | None = None,
) -> UnsupportedClaimEvaluation:
    """Thin typed wrapper; v1 does not emit per-span classifications."""
    raw = evaluate_unsupported_claims_v1(response, allowed_keys, supporting_source_texts)
    return UnsupportedClaimEvaluation(
        evaluator_version=EVALUATOR_VERSION,
        spans=[],
        unsupported_flag_count=int(raw["unsupported_claim_count"]),
        analyzed_claim_count=0,
        uncertain_count=0,
        notes=str(raw["notes"]),
    )
