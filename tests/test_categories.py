"""Tests for CobraBench category weights."""

from __future__ import annotations

from cobra_core.schemas.categories import (
    CATEGORY_WEIGHTS,
    CATEGORY_WEIGHTS_V02,
    BenchmarkCategory,
    weights_sum,
    weights_sum_v02,
)


def test_all_required_v01_categories_present() -> None:
    expected = {
        BenchmarkCategory.INVESTIGATION_REASONING,
        BenchmarkCategory.EVIDENCE_GROUNDING,
        BenchmarkCategory.CITATION_CORRECTNESS,
        BenchmarkCategory.HALLUCINATION_RESISTANCE,
        BenchmarkCategory.CONTRADICTION_DETECTION,
        BenchmarkCategory.LONG_DOCUMENT_ANALYSIS,
        BenchmarkCategory.CODING,
        BenchmarkCategory.REFUSAL_QUALITY,
        BenchmarkCategory.INSTRUCTION_FOLLOWING,
    }
    assert set(CATEGORY_WEIGHTS) == expected


def test_weights_sum_to_one() -> None:
    assert abs(weights_sum() - 1.0) < 1e-9


def test_initial_weight_values() -> None:
    assert CATEGORY_WEIGHTS[BenchmarkCategory.INVESTIGATION_REASONING] == 0.20
    assert CATEGORY_WEIGHTS[BenchmarkCategory.EVIDENCE_GROUNDING] == 0.15
    assert CATEGORY_WEIGHTS[BenchmarkCategory.HALLUCINATION_RESISTANCE] == 0.15
    assert CATEGORY_WEIGHTS[BenchmarkCategory.CITATION_CORRECTNESS] == 0.15
    assert CATEGORY_WEIGHTS[BenchmarkCategory.CONTRADICTION_DETECTION] == 0.10
    assert CATEGORY_WEIGHTS[BenchmarkCategory.CODING] == 0.10
    assert CATEGORY_WEIGHTS[BenchmarkCategory.LONG_DOCUMENT_ANALYSIS] == 0.05
    assert CATEGORY_WEIGHTS[BenchmarkCategory.REFUSAL_QUALITY] == 0.05
    assert CATEGORY_WEIGHTS[BenchmarkCategory.INSTRUCTION_FOLLOWING] == 0.05


def test_v02_weights_include_uncertainty_and_sum_to_one() -> None:
    assert BenchmarkCategory.UNCERTAINTY_CALIBRATION in CATEGORY_WEIGHTS_V02
    assert abs(weights_sum_v02() - 1.0) < 1e-9
    assert len(CATEGORY_WEIGHTS_V02) == 10
