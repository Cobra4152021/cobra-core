"""CobraBench category taxonomy and initial weighted scoring configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class BenchmarkCategory(StrEnum):
    """Categories measured by CobraBench in Phase 1."""

    INVESTIGATION_REASONING = "investigation_reasoning"
    EVIDENCE_GROUNDING = "evidence_grounding"
    CITATION_CORRECTNESS = "citation_correctness"
    HALLUCINATION_RESISTANCE = "hallucination_resistance"
    CONTRADICTION_DETECTION = "contradiction_detection"
    LONG_DOCUMENT_ANALYSIS = "long_document_analysis"
    CODING = "coding"
    REFUSAL_QUALITY = "refusal_quality"
    INSTRUCTION_FOLLOWING = "instruction_following"


# Initial weighted scoring configuration (must sum to 1.0).
# Scores always retain category-level detail; never reduce an evaluation
# to a single unexplained number.
CATEGORY_WEIGHTS: Final[dict[BenchmarkCategory, float]] = {
    BenchmarkCategory.INVESTIGATION_REASONING: 0.20,
    BenchmarkCategory.EVIDENCE_GROUNDING: 0.15,
    BenchmarkCategory.HALLUCINATION_RESISTANCE: 0.15,
    BenchmarkCategory.CITATION_CORRECTNESS: 0.15,
    BenchmarkCategory.CONTRADICTION_DETECTION: 0.10,
    BenchmarkCategory.CODING: 0.10,
    BenchmarkCategory.LONG_DOCUMENT_ANALYSIS: 0.05,
    BenchmarkCategory.REFUSAL_QUALITY: 0.05,
    BenchmarkCategory.INSTRUCTION_FOLLOWING: 0.05,
}


def weights_sum() -> float:
    """Return the sum of category weights (expected: 1.0)."""
    return sum(CATEGORY_WEIGHTS.values())
