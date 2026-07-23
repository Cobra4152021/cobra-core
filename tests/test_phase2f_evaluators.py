"""Phase 2F evaluator / parser / registry tests (no model load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import (
    BaselineLockError,
    assert_path_outside_locked_baseline,
    load_baseline_lock,
    validate_baseline_lock,
)
from cobra_core.evaluators.citations.v2 import evaluate_citations_v2, validate_citation_keys
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2
from cobra_core.evaluators.format_compliance.parser import ParserMode, parse_finding_risk_next
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2
from cobra_core.evaluators.registry import list_evaluator_versions, load_evaluator_metadata
from cobra_core.evaluators.telemetry.output_budget import (
    CompletionClass,
    classify_output_budget,
)
from cobra_core.evaluators.unsupported_claims.types import ClaimClass, SupportState
from cobra_core.evaluators.unsupported_claims.v1 import evaluate_unsupported_claims_v1
from cobra_core.evaluators.unsupported_claims.v2 import (
    classify_span,
    evaluate_unsupported_claims_v2,
)
from cobra_core.prompts.registry import load_prompt_template, validate_prompt_registry
from cobra_core.runtime_policies.loader import load_runtime_profile, validate_runtime_registry
from cobra_core.schemas.benchmark_v02 import BenchmarkCaseV02

ROOT = Path(__file__).resolve().parents[1]
BASELINE_LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
BASELINE_RUN = ROOT / "evaluations/results/cobrabench-v0.1/qwen3-8b/20260722T200000Z-8bba5e01"
FIXTURES = ROOT / "evaluations/fixtures/unsupported-claims-v2/fixtures.json"
METRICS = ROOT / "evaluations/fixtures/unsupported-claims-v2/metrics.json"
DRAFT_DIR = ROOT / "benchmarks/drafts/cobrabench-v0.2"
OFFLINE_JSON = ROOT / "evaluations/analysis/qwen3-8b-offline-reevaluation-v2.json"


def test_evaluator_registry_versioning() -> None:
    versions = list_evaluator_versions()
    assert "1.0.0" in versions["unsupported_claims"]
    assert "2.0.0" in versions["unsupported_claims"]
    v1 = load_evaluator_metadata("unsupported_claims", "1.0.0")
    v2 = load_evaluator_metadata("unsupported_claims", "2.0.0")
    assert v1.used_by_official_cobrabench_v01 is True
    assert v1.deprecated is True
    assert v2.used_by_official_cobrabench_v01 is False


def test_v1_immutability_still_flags_uncited_sentences() -> None:
    text = "The server was deleted without approval."
    v1 = evaluate_unsupported_claims_v1(text, ["SRC-A"], {"SRC-A": "No deletion recorded."})
    assert v1["unsupported_claim_count"] >= 1
    assert v1["evaluator_version"] == "1.0.0"


def test_claim_classification_categories() -> None:
    sources = {"SRC-A": "Scanner found one outdated dependency in demo app."}
    assert (
        classify_span("## Findings", allowed_keys=["SRC-A"], sources=sources) == ClaimClass.HEADING
    )
    assert classify_span(
        "Therefore the next step is unclear.", allowed_keys=["SRC-A"], sources=sources
    ) in {
        ClaimClass.CONNECTIVE_LANGUAGE,
        ClaimClass.UNCERTAINTY_STATEMENT,
        ClaimClass.EXPLICITLY_LABELED_INFERENCE,
    }
    assert (
        classify_span(
            "We recommend verifying the patch window.",
            allowed_keys=["SRC-A"],
            sources=sources,
        )
        == ClaimClass.RECOMMENDATION
    )
    para = classify_span(
        "Scanner found one outdated dependency in demo app [SRC-A].",
        allowed_keys=["SRC-A"],
        sources=sources,
    )
    assert para == ClaimClass.EVIDENCE_PARAPHRASE


def test_supported_paraphrase_and_inference_not_flagged() -> None:
    sources = {"SRC-A": "Alex Chen approved change CHG-44 on 2024-02-02."}
    text = (
        "Alex Chen approved change CHG-44 on 2024-02-02 [SRC-A]. "
        "Inference: the change may have been urgent, but that is not confirmed."
    )
    result = evaluate_unsupported_claims_v2(text, ["SRC-A"], sources)
    assert result.unsupported_flag_count == 0
    classes = {s.claim_class for s in result.spans}
    assert (
        ClaimClass.EVIDENCE_PARAPHRASE in classes
        or ClaimClass.EXPLICITLY_LABELED_INFERENCE in classes
    )


def test_structural_and_recommendation_exclusion() -> None:
    text = "**Supported Findings:**\n\nNext step: request badge logs."
    result = evaluate_unsupported_claims_v2(text, ["SRC-A"], {"SRC-A": "badge entry 09:01"})
    assert all(not s.flagged_as_unsupported for s in result.spans)


def test_evidence_id_linkage() -> None:
    sources = {"SRC-A": "count is 120 units", "SRC-B": "count is 95 units"}
    text = "Report A states 120 units [SRC-A] while Report B states 95 units [SRC-B]."
    result = evaluate_unsupported_claims_v2(text, ["SRC-A", "SRC-B"], sources)
    linked = {k for s in result.spans for k in s.cited_keys}
    assert "SRC-A" in linked and "SRC-B" in linked


@pytest.mark.skipif(not METRICS.is_file(), reason="fixture metrics missing")
def test_unsupported_claim_v2_fixture_metrics() -> None:
    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    assert metrics["fixture_count"] >= 50
    assert metrics["v2"]["false_positive_rate"] < 0.25
    assert metrics["v2"]["false_positive_rate"] < metrics["v1_false_positive_rate_on_audit_sample"]
    assert metrics["acceptance"]["materially_outperforms_v1"] is True


def test_semantic_versus_exact_scoring() -> None:
    markdown = (
        "- **FINDING:** Scanner found one outdated dependency.\n"
        "- **RISK:** Security exposure from outdated package.\n"
        "- **NEXT:** Update the dependency.\n"
    )
    result = evaluate_format_compliance_v2(markdown)
    assert result.semantic_score >= 0.66
    assert result.exact_format_score < 1.0
    assert result.tolerant_parse_success is True
    assert result.parse_success is False


def test_strict_and_tolerant_parser_behavior() -> None:
    strict_text = "FINDING: a\nRISK: b\nNEXT: c\n"
    strict = parse_finding_risk_next(strict_text, mode=ParserMode.STRICT)
    assert strict.success is True
    tolerant = parse_finding_risk_next(
        "- **FINDING:** a\n- **RISK:** b\n- **NEXT:** c\n",
        mode=ParserMode.TOLERANT,
    )
    assert tolerant.success is True
    assert "accept_markdown_bullets" in tolerant.transformations_applied


def test_tolerant_parser_does_not_invent_missing_fields() -> None:
    partial = "FINDING: only one field present\n"
    result = parse_finding_risk_next(partial, mode=ParserMode.TOLERANT)
    assert result.success is False
    assert "RISK" in result.missing_fields
    assert "NEXT" in result.missing_fields
    assert "RISK" not in result.fields


def test_citation_precision_and_coverage_metrics() -> None:
    text = "Approved by Alex [SRC-A]. Optional chatter ignored."
    metrics = evaluate_citations_v2(
        text,
        allowed_keys=["SRC-A", "SRC-B"],
        required_evidence_ids=["SRC-A"],
        optional_evidence_ids=["SRC-B"],
        contrary_evidence_ids=["SRC-B"],
    )
    assert metrics.citation_precision == 1.0
    assert metrics.evidence_coverage == 1.0
    assert metrics.contrary_evidence_coverage == 0.0
    issues = validate_citation_keys("See SRC-ZZ", allowed_keys=["SRC-A"])
    assert any(i.issue_type == "unknown_key" for i in issues)


def test_contradiction_submetrics_vector() -> None:
    text = (
        "SRC-A and SRC-B contradict: 120 versus 95 units. "
        "Request a recount as additional evidence. Confidence is uncertain."
    )
    result = evaluate_contradictions_v2(text)
    assert result.detection >= 0.5
    assert result.numerical_comparison >= 0.5
    assert result.resolution_evidence_recommendation >= 0.5
    data = result.model_dump()
    for key in (
        "detection",
        "localization",
        "classification",
        "explanation",
        "numerical_comparison",
        "timeline_comparison",
        "preservation_of_competing_accounts",
        "avoidance_of_invented_reconciliation",
        "resolution_evidence_recommendation",
        "confidence_calibration",
    ):
        assert key in data


def test_output_budget_natural_vs_truncation() -> None:
    natural = classify_output_budget(
        response="Key facts listed. Exceptions noted.",
        requested_max_output_tokens=512,
        actual_output_tokens=128,
        finish_reason="completed",
        required_sections=["Key", "Exceptions"],
    )
    assert natural.completion_class in {
        CompletionClass.LIKELY_NATURAL_COMPLETION,
        CompletionClass.STOPPED_AFTER_CONCLUSION,
        CompletionClass.UNKNOWN,
    }
    assert natural.completion_class != CompletionClass.LIKELY_BUDGET_EXHAUSTION

    truncated = classify_output_budget(
        response="Still writing without ending",
        requested_max_output_tokens=512,
        actual_output_tokens=512,
        finish_reason="length",
        required_sections=["KeyFacts"],
    )
    assert truncated.completion_class == CompletionClass.LIKELY_BUDGET_EXHAUSTION


def test_prompt_and_runtime_registry_validation() -> None:
    assert validate_prompt_registry() == []
    assert validate_runtime_registry() == []
    tmpl = load_prompt_template("exact-format", "2.0.0")
    assert tmpl.version == "2.0.0"
    profile = load_runtime_profile("long-document-analysis")
    assert profile.max_output_tokens >= 1024


def test_cobrabench_v02_draft_schema_examples() -> None:
    files = sorted(DRAFT_DIR.glob("draft-*.json"))
    assert len(files) >= 4
    for path in files:
        case = BenchmarkCaseV02.model_validate_json(path.read_text(encoding="utf-8"))
        assert case.official_release is False
        assert case.scored is False
        assert case.frozen is False
        assert case.part_of_cobrabench_v01 is False


@pytest.mark.skipif(not BASELINE_LOCK.is_file(), reason="baseline lock missing")
def test_immutable_baseline_write_protection_and_hash() -> None:
    lock = load_baseline_lock(BASELINE_LOCK)
    assert (
        lock.result_inventory_hash
        == "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
    )
    if BASELINE_RUN.is_dir():
        assert validate_baseline_lock(lock, repo_root=ROOT) == []
    with pytest.raises(BaselineLockError):
        assert_path_outside_locked_baseline(
            BASELINE_LOCK,
            BASELINE_RUN / "v2-metrics.json",
            repo_root=ROOT,
        )


def test_score_version_compatibility_docs_and_offline_separation() -> None:
    compat = (ROOT / "docs/EVALUATOR_VERSIONING_AND_SCORE_COMPATIBILITY.md").read_text(
        encoding="utf-8"
    )
    assert "not" in compat.lower() and "comparable" in compat.lower()
    adr = (ROOT / "docs/decisions/ADR-0005-prompt-runtime-evaluator-improvements.md").read_text(
        encoding="utf-8"
    )
    assert "does not change the official CobraBench v0.1 baseline" in adr
    if OFFLINE_JSON.is_file():
        data = json.loads(OFFLINE_JSON.read_text(encoding="utf-8"))
        assert "Offline evaluator-v2 diagnostic results" in data["label"]
        assert data["official_baseline_score_unchanged"] == 0.84


def test_support_state_enum_coverage() -> None:
    assert SupportState.UNSUPPORTED.value == "unsupported"
    assert ClaimClass.STRUCTURAL_TEXT.value == "structural_text"
