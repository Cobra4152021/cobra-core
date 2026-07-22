"""Tests for objective and behavior rule checks."""

from __future__ import annotations

from cobra_core.evaluation.rule_checks import (
    run_objective_checks,
    run_rule_based_behavior_checks,
    score_from_checks,
)
from cobra_core.schemas.benchmark import BenchmarkCase, ObjectiveCheck, ObjectiveCheckType


def _case(**overrides: object) -> BenchmarkCase:
    data = {
        "case_id": "cb-test-rules",
        "version": "0.1.0",
        "category": "instruction_following",
        "title": "Rules test",
        "system_prompt": "Follow instructions.",
        "user_prompt": "Respond.",
        "supporting_sources": [],
        "expected_behaviors": [
            {"behavior_id": "exp-a", "description": "Keywords: FINDING, RISK", "required": True}
        ],
        "prohibited_behaviors": [
            {"behavior_id": "pro-a", "description": "Keywords: DROP DATABASE"}
        ],
        "scoring_rubric": {"rubric_id": "cobrabench_weighted_v1", "rubric_version": "1.0.0"},
        "objective_checks": [
            ObjectiveCheck(
                check_id="obj-json",
                description="Response body is valid JSON with required keys.",
                check_type=ObjectiveCheckType.JSON_PARSE,
            ),
            ObjectiveCheck(
                check_id="obj-exact",
                description='Optional exact. Exact:{"status":"ok"}',
                check_type=ObjectiveCheckType.EXACT_MATCH_OPTIONAL,
            ),
        ],
    }
    data.update(overrides)
    return BenchmarkCase.model_validate(data)


def test_json_parse_check() -> None:
    case = _case()
    checks = run_objective_checks(case, '{"status":"ok","source":"SRC-A","note":"x"}')
    assert checks[0]["passed"] is True


def test_exact_match_optional_without_exact_passes() -> None:
    case = _case(
        objective_checks=[
            ObjectiveCheck(
                check_id="obj-exact",
                description="No exact configured.",
                check_type=ObjectiveCheckType.EXACT_MATCH_OPTIONAL,
            )
        ]
    )
    checks = run_objective_checks(case, "anything")
    assert checks[0]["passed"] is True


def test_behavior_checks_and_score() -> None:
    case = _case()
    checks = run_rule_based_behavior_checks(case, "FINDING: x\nRISK: y")
    assert any(c["behavior_id"] == "exp-a" and c["passed"] for c in checks)
    assert score_from_checks(checks) == 1.0


def test_score_from_checks_empty_is_perfect() -> None:
    assert score_from_checks([]) == 1.0
