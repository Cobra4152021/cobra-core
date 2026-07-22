"""Tests for blinded comparison helpers."""

from __future__ import annotations

import json

from cobra_core.evaluation.comparison import (
    blind_model_label,
    compare_category_scores,
    compare_weighted_totals,
    weighted_total,
)
from cobra_core.schemas.categories import BenchmarkCategory


def test_blind_model_label() -> None:
    assert blind_model_label(0) == "Model-A"
    assert blind_model_label(1) == "Model-B"


def test_compare_category_scores_material_delta() -> None:
    a = {"investigation_reasoning": 0.5}
    b = {"investigation_reasoning": 0.62}
    result = compare_category_scores(a, b, material_threshold=0.05)
    assert "investigation_reasoning" in result["material_deltas"]
    assert result["deltas_b_minus_a"]["investigation_reasoning"] == 0.12


def test_weighted_total_without_winner() -> None:
    scores = {category.value: 0.8 for category in BenchmarkCategory}
    total = weighted_total(scores)
    assert total == 0.8
    comparison = compare_weighted_totals(scores, scores)
    assert comparison["delta_b_minus_a"] == 0.0
    assert "winner" not in json.dumps(comparison).lower()
