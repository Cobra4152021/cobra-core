"""CobraBench category taxonomy and initial weighted scoring configuration."""

from __future__ import annotations

from enum import StrEnum
from typing import Final


class BenchmarkCategory(StrEnum):
    """Categories measured by CobraBench."""

    INVESTIGATION_REASONING = "investigation_reasoning"
    EVIDENCE_GROUNDING = "evidence_grounding"
    CITATION_CORRECTNESS = "citation_correctness"
    HALLUCINATION_RESISTANCE = "hallucination_resistance"
    CONTRADICTION_DETECTION = "contradiction_detection"
    LONG_DOCUMENT_ANALYSIS = "long_document_analysis"
    CODING = "coding"
    REFUSAL_QUALITY = "refusal_quality"
    INSTRUCTION_FOLLOWING = "instruction_following"
    UNCERTAINTY_CALIBRATION = "uncertainty_calibration"


# Initial weighted scoring configuration for CobraBench v0.1 (must sum to 1.0).
# Scores always retain category-level detail; never reduce an evaluation
# to a single unexplained number.
# Note: v0.1 cases do not use UNCERTAINTY_CALIBRATION as a primary category.
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


# CobraBench v0.2 weights (must sum to 1.0). Independent of v0.1.
CATEGORY_WEIGHTS_V02: Final[dict[BenchmarkCategory, float]] = {
    BenchmarkCategory.INVESTIGATION_REASONING: 0.18,
    BenchmarkCategory.EVIDENCE_GROUNDING: 0.14,
    BenchmarkCategory.HALLUCINATION_RESISTANCE: 0.14,
    BenchmarkCategory.CITATION_CORRECTNESS: 0.14,
    BenchmarkCategory.CONTRADICTION_DETECTION: 0.12,
    BenchmarkCategory.CODING: 0.08,
    BenchmarkCategory.LONG_DOCUMENT_ANALYSIS: 0.06,
    BenchmarkCategory.INSTRUCTION_FOLLOWING: 0.05,
    BenchmarkCategory.UNCERTAINTY_CALIBRATION: 0.05,
    BenchmarkCategory.REFUSAL_QUALITY: 0.04,
}


def weights_sum() -> float:
    """Return the sum of v0.1 category weights (expected: 1.0)."""
    return sum(CATEGORY_WEIGHTS.values())


def weights_sum_v02() -> float:
    """Return the sum of v0.2 category weights (expected: 1.0)."""
    return sum(CATEGORY_WEIGHTS_V02.values())
