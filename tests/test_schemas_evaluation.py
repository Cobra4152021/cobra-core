"""EvaluationRun and scoring aggregation tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from cobra_core.evaluation.scoring import aggregate_category_scores
from cobra_core.schemas.categories import BenchmarkCategory
from cobra_core.schemas.evaluation import (
    EvaluationRun,
    EvaluatorKind,
    EvaluatorScore,
    InferenceSettings,
    ScoreBreakdown,
)


def test_llm_as_judge_marked_advisory() -> None:
    score = EvaluatorScore(
        category=BenchmarkCategory.CITATION_CORRECTNESS,
        kind=EvaluatorKind.LLM_AS_JUDGE,
        score=0.8,
        rationale="Advisory judgment only",
        evaluator_version="judge-0.0.1",
    )
    assert score.is_advisory is True


def test_aggregate_prefers_rule_based_over_llm_judge() -> None:
    scores = [
        EvaluatorScore(
            category=BenchmarkCategory.EVIDENCE_GROUNDING,
            kind=EvaluatorKind.LLM_AS_JUDGE,
            score=0.9,
            rationale="Judge liked it",
            evaluator_version="judge-0.0.1",
        ),
        EvaluatorScore(
            category=BenchmarkCategory.EVIDENCE_GROUNDING,
            kind=EvaluatorKind.RULE_BASED,
            score=0.4,
            rationale="Missed required citation",
            evaluator_version="rules-0.0.1",
        ),
    ]
    breakdown = aggregate_category_scores(scores)
    assert breakdown.by_category[BenchmarkCategory.EVIDENCE_GROUNDING] == 0.4


def test_score_breakdown_retains_categories() -> None:
    breakdown = ScoreBreakdown(
        by_category={
            BenchmarkCategory.INVESTIGATION_REASONING: 0.7,
            BenchmarkCategory.EVIDENCE_GROUNDING: 0.8,
        }
    )
    assert BenchmarkCategory.INVESTIGATION_REASONING in breakdown.by_category
    assert breakdown.weighted_overall() is None  # incomplete categories


def test_evaluation_run_requires_category_detail() -> None:
    scores = [
        EvaluatorScore(
            category=BenchmarkCategory.CODING,
            kind=EvaluatorKind.OBJECTIVE,
            score=1.0,
            rationale="Unit checks passed",
            evaluator_version="obj-0.0.1",
        )
    ]
    breakdown = ScoreBreakdown(by_category={BenchmarkCategory.CODING: 1.0})
    run = EvaluationRun(
        run_id="run-001",
        timestamp=datetime.now(UTC),
        model_manifest_ref="model-cards/EXAMPLE_qwen_manifest.json",
        model_revision="not-acquired",
        benchmark_version="1.0.0",
        case_id="cb-001-evidence-grounded-investigation",
        system_prompt="sys",
        user_prompt="user",
        inference_settings=InferenceSettings(temperature=0.0, seed=42),
        raw_response_location="evaluations/results/run-001/raw.txt",
        deterministic_seed=42,
        evaluator_scores=scores,
        score_breakdown=breakdown,
        overall_score=None,
        evaluator_version="eval-bundle-0.1.0",
    )
    assert run.score_breakdown.by_category[BenchmarkCategory.CODING] == 1.0
    assert run.overall_score is None


def test_overall_score_must_match_breakdown() -> None:
    scores = [
        EvaluatorScore(
            category=cat,
            kind=EvaluatorKind.HUMAN,
            score=1.0,
            rationale="full marks",
            evaluator_version="human-0.0.1",
        )
        for cat in BenchmarkCategory
    ]
    breakdown = ScoreBreakdown(by_category=dict.fromkeys(BenchmarkCategory, 1.0))
    with pytest.raises(ValidationError):
        EvaluationRun(
            run_id="run-bad-overall",
            timestamp=datetime.now(UTC),
            model_manifest_ref="model-cards/EXAMPLE_qwen_manifest.json",
            model_revision="not-acquired",
            benchmark_version="1.0.0",
            case_id="cb-001-evidence-grounded-investigation",
            system_prompt="sys",
            user_prompt="user",
            inference_settings=InferenceSettings(),
            raw_response_location="evaluations/results/run-bad/raw.txt",
            evaluator_scores=scores,
            score_breakdown=breakdown,
            overall_score=0.5,
            evaluator_version="eval-bundle-0.1.0",
        )
