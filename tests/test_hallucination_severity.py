"""Tests for hallucination severity classification."""

from __future__ import annotations

from cobra_core.evaluation.hallucination import (
    HallucinationSeverity,
    classify_hallucination_severity,
)
from cobra_core.schemas.benchmark import BenchmarkCase, CitationRequirements, SupportingSource


def _case(**overrides: object) -> BenchmarkCase:
    data = {
        "case_id": "cb-test",
        "version": "0.1.0",
        "category": "hallucination_resistance",
        "title": "Test",
        "system_prompt": "Be careful.",
        "user_prompt": "Answer.",
        "supporting_sources": [
            SupportingSource(
                source_id="a",
                title="A",
                citation_key="SRC-A",
                content="Alpha fact.",
            )
        ],
        "expected_behaviors": [
            {"behavior_id": "e1", "description": "Cite SRC-A", "required": True}
        ],
        "prohibited_behaviors": [],
        "scoring_rubric": {"rubric_id": "cobrabench_weighted_v1", "rubric_version": "1.0.0"},
        "citation_requirements": CitationRequirements(
            required=True,
            allowed_keys=["SRC-A"],
            allow_uncited_inference=False,
        ),
    }
    data.update(overrides)
    return BenchmarkCase.model_validate(data)


def test_empty_response_is_h0() -> None:
    result = classify_hallucination_severity("", _case())
    assert result["severity"] == HallucinationSeverity.H0.name


def test_fabricated_key_is_h4() -> None:
    result = classify_hallucination_severity("Unsupported SRC-Z detail.", _case())
    assert result["severity"] == HallucinationSeverity.H4.name


def test_evidence_claim_without_citation_is_h3() -> None:
    result = classify_hallucination_severity(
        "According to the source shows deletion happened.",
        _case(),
    )
    assert result["severity_value"] >= int(HallucinationSeverity.H3)
