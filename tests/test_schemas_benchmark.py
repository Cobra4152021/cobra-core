"""BenchmarkCase schema and case file validation tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from cobra_core.schemas.benchmark import BenchmarkCase
from cobra_core.validation import validate_json_dir

REQUIRED_CASE_IDS = {
    "cb-001-evidence-grounded-investigation",
    "cb-002-contradictory-witness-statements",
    "cb-003-citation-unsupported-claim-detection",
}


def _valid_case(**overrides: object) -> dict[str, object]:
    data: dict[str, object] = {
        "case_id": "cb-test-case",
        "version": "1.0.0",
        "category": "investigation_reasoning",
        "title": "Test case",
        "system_prompt": "Be careful.",
        "user_prompt": "Analyze the sources.",
        "supporting_sources": [],
        "expected_behaviors": [
            {
                "behavior_id": "exp-1",
                "description": "Cites sources",
                "required": True,
            }
        ],
        "prohibited_behaviors": [],
        "scoring_rubric": {
            "rubric_id": "cobrabench_weighted_v1",
            "rubric_version": "1.0.0",
        },
        "sensitivity": "public_synthetic",
        "tags": ["Synthetic", "test", "test"],
    }
    data.update(overrides)
    return data


def test_valid_case_accepted_and_tags_normalized() -> None:
    case = BenchmarkCase.model_validate(_valid_case())
    assert case.tags == ["synthetic", "test"]


def test_synthetic_cases_validate_and_include_required_ids(cases_dir: Path) -> None:
    cases, issues = validate_json_dir(cases_dir, BenchmarkCase)
    assert issues == []
    case_ids = {c.case_id for c in cases}
    assert REQUIRED_CASE_IDS.issubset(case_ids)
    assert len(cases) >= 28
    assert all(c.sensitivity.value == "public_synthetic" for c in cases)


def test_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCase.model_validate(_valid_case(category="vibes_only"))


def test_rejects_missing_expected_behaviors() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCase.model_validate(_valid_case(expected_behaviors=[]))


def test_rejects_bad_case_id() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCase.model_validate(_valid_case(case_id="BAD CASE"))
