"""Phase 2E static analysis tests (no model load)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from cobra_core.analysis.audit_metrics import (
    false_positive_rate,
    mean_absolute_difference,
    precision,
    validate_format_failure_class,
)
from cobra_core.analysis.baseline_lock import (
    BaselineLockError,
    BaselineLockRecord,
    assert_baseline_not_overwritten,
    assert_path_outside_locked_baseline,
    compute_run_inventory_hash,
    load_baseline_lock,
    validate_baseline_lock,
)
from cobra_core.analysis.case_analysis import build_case_analyses
from cobra_core.analysis.diagnostics import (
    DiagnosticSuiteError,
    assert_diagnostic_run_separated,
    load_diagnostic_suite,
    validate_diagnostic_suite,
)
from cobra_core.analysis.fix_classes import (
    FixClass,
    FixProposal,
    validate_class4_eligibility,
)
from cobra_core.analysis.weakness import (
    CaseWeaknessAnalysis,
    ConfidenceLevel,
    DiagnosticPriority,
    WeaknessClass,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_RUN = (
    ROOT / "evaluations" / "results" / "cobrabench-v0.1" / "qwen3-8b" / "20260722T200000Z-8bba5e01"
)
BASELINE_LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
CASE_ANALYSIS = ROOT / "evaluations/analysis/qwen3-8b-v0.1-case-analysis.json"
BLOCKED_DIAG = ROOT / "evaluations/analysis/phase2e-blocked-diagnostic-run.json"
COHORTS = ROOT / "benchmarks/diagnostics/qwen3-8b-phase-2e/cohorts.json"
V02_PROPOSAL = ROOT / "docs/COBRABENCH_V0_2_PROPOSAL.md"
ADR4 = ROOT / "docs/decisions/ADR-0004-qwen3-8b-weakness-analysis.md"
STATUS = ROOT / "docs/PHASE_2E_STATUS.md"
MATRIX = ROOT / "evaluations/reports/QWEN3_8B_WEAKNESS_MATRIX.md"


def test_weakness_class_codes() -> None:
    assert WeaknessClass.MODEL_CAPABILITY.value == "M"
    assert WeaknessClass.RUNTIME_QUANTIZATION.value == "R"
    assert WeaknessClass.PROMPT_TEMPLATE.value == "P"
    assert WeaknessClass.OUTPUT_LENGTH.value == "L"
    assert WeaknessClass.BENCHMARK_DEFECT.value == "B"
    assert WeaknessClass.SCORING_PARSER.value == "S"
    assert WeaknessClass.HUMAN_REVIEW.value == "H"
    assert WeaknessClass.UNKNOWN.value == "U"
    assert len(WeaknessClass) == 8


def test_case_weakness_analysis_schema_validation() -> None:
    item = CaseWeaknessAnalysis(
        case_id="cb-001-evidence-grounded-investigation",
        category="evidence_grounding",
        baseline_score=0.88,
        rule_failures=["beh:pro-invent-transfer"],
        human_findings="Strong grounding.",
        output_length_chars=1200,
        finish_reason="completed",
        input_tokens=368,
        output_tokens=512,
        latency_ms=90000.0,
        citation_metrics={"unsupported_claim_count": 20},
        hallucination_severity_human="H0",
        hallucination_severity_automated="H3",
        observed_weakness="none material",
        primary_weakness_class=None,
        contributing_classes=[WeaknessClass.OUTPUT_LENGTH, WeaknessClass.SCORING_PARSER],
        confidence=ConfidenceLevel.HIGH,
        diagnostic_priority=DiagnosticPriority.NONE,
        rerun_justified=False,
        evidence=["output_token_count=512"],
        diagnostic_test="Output-cap cohort",
    )
    assert item.contributing_classes[0] == WeaknessClass.OUTPUT_LENGTH


@pytest.mark.skipif(not BASELINE_RUN.is_dir(), reason="baseline run directory not present")
def test_build_case_analyses_count_and_schema() -> None:
    analyses = build_case_analyses(BASELINE_RUN)
    assert len(analyses) == 28
    for item in analyses:
        CaseWeaknessAnalysis.model_validate(item.model_dump())
        assert item.case_id.startswith("cb-")


@pytest.mark.skipif(not CASE_ANALYSIS.is_file(), reason="case analysis artifact missing")
def test_case_level_cause_classification_artifact() -> None:
    data = json.loads(CASE_ANALYSIS.read_text(encoding="utf-8"))
    assert data["case_count"] == 28
    assert data["run_id"] == "20260722T200000Z-8bba5e01"
    primaries = {c.get("primary_weakness_class") for c in data["cases"]}
    allowed = {None, *{m.value for m in WeaknessClass}}
    assert primaries <= allowed
    for case in data["cases"]:
        CaseWeaknessAnalysis.model_validate(case)


@pytest.mark.skipif(not BASELINE_RUN.is_dir(), reason="baseline run directory not present")
def test_long_document_cases_not_at_token_cap() -> None:
    analyses = {a.case_id: a for a in build_case_analyses(BASELINE_RUN)}
    cb23 = analyses["cb-023-long-memo-key-facts"]
    cb24 = analyses["cb-024-long-policy-exceptions"]
    assert cb23.output_tokens == 127
    assert cb24.output_tokens == 128
    assert cb23.finish_reason == "completed"
    assert cb24.finish_reason == "completed"


def test_baseline_lock_refuse_overwrite(tmp_path: Path) -> None:
    run_dir = tmp_path / "locked-run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        json.dumps({"run_id": "test-run", "cases": []}) + "\n",
        encoding="utf-8",
    )
    inventory_hash = compute_run_inventory_hash(run_dir)
    lock_path = tmp_path / "baseline-lock.json"
    record = BaselineLockRecord(
        lock_id="test-lock",
        run_id="test-run",
        model_slug="qwen3-8b",
        model_revision="abc123",
        benchmark_version="0.1",
        artifact_inventory_ref="model-cards/qwen/qwen3-8b.manifest.json",
        benchmark_release_hash="release-hash",
        protocol_path="evaluations/protocols/qwen3-8b-cobrabench-v0.1.json",
        protocol_hash="protocol-hash",
        result_run_path=str(run_dir),
        result_inventory_hash=inventory_hash,
        scoring_implementation_version="cobrabench-evaluator-v0.1.0",
        human_review_version="human-interim-reviewer-v0.1",
        report_references=[],
        created_at=datetime.now(UTC),
        immutable=True,
    )
    lock_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    with pytest.raises(BaselineLockError, match="Refusing to overwrite locked baseline"):
        assert_baseline_not_overwritten(lock_path, run_dir)
    other_run = tmp_path / "other-run"
    other_run.mkdir()
    assert_baseline_not_overwritten(lock_path, other_run)


def test_analysis_artifacts_cannot_write_into_locked_baseline(tmp_path: Path) -> None:
    run_dir = tmp_path / "locked-run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        json.dumps({"run_id": "test-run", "cases": []}) + "\n",
        encoding="utf-8",
    )
    lock_path = tmp_path / "baseline-lock.json"
    record = BaselineLockRecord(
        lock_id="test-lock",
        run_id="test-run",
        model_slug="qwen3-8b",
        model_revision="abc123",
        benchmark_version="0.1",
        artifact_inventory_ref="ref",
        benchmark_release_hash="release-hash",
        protocol_path="evaluations/protocols/qwen3-8b-cobrabench-v0.1.json",
        protocol_hash="protocol-hash",
        result_run_path=str(run_dir),
        result_inventory_hash=compute_run_inventory_hash(run_dir),
        scoring_implementation_version="v0.1",
        human_review_version="v0.1",
        report_references=[],
        created_at=datetime.now(UTC),
        immutable=True,
    )
    lock_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")

    nested = run_dir / "human-consistency-check.json"
    with pytest.raises(BaselineLockError, match="Refusing to write analysis artifact"):
        assert_path_outside_locked_baseline(lock_path, nested)

    safe = tmp_path / "analysis" / "human-consistency-check.json"
    assert_path_outside_locked_baseline(lock_path, safe)


@pytest.mark.skipif(not BASELINE_LOCK.is_file(), reason="baseline lock missing")
def test_committed_baseline_lock_immutable_and_valid() -> None:
    record = load_baseline_lock(BASELINE_LOCK)
    assert record.immutable is True
    assert record.run_id == "20260722T200000Z-8bba5e01"
    assert (
        record.result_inventory_hash
        == "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
    )
    if BASELINE_RUN.is_dir():
        assert validate_baseline_lock(record, repo_root=ROOT) == []
        assert not (BASELINE_RUN / "human-consistency-check.json").exists()


@pytest.mark.skipif(not BLOCKED_DIAG.is_file(), reason="blocked diagnostic record missing")
def test_blocked_diagnostic_run_metadata() -> None:
    data = json.loads(BLOCKED_DIAG.read_text(encoding="utf-8"))
    assert data["run_id"] == "20260722T220000Z-2ediag01"
    assert data["generations_completed"] == 0
    assert data["new_run_id_required"] is True
    assert data["crash_code"] == "0xC0000005"


def test_diagnostic_run_separation() -> None:
    baseline = ROOT / "evaluations/results/cobrabench-v0.1/qwen3-8b/20260722T200000Z-8bba5e01"
    diag = ROOT / "evaluations/results/diagnostics/qwen3-8b-phase-2e/20260722T220000Z-2ediag01"
    assert_diagnostic_run_separated(
        "20260722T220000Z-2ediag01",
        baseline_run_id="20260722T200000Z-8bba5e01",
        diagnostic_root=diag,
        baseline_root=baseline,
    )
    with pytest.raises(DiagnosticSuiteError, match="must differ"):
        assert_diagnostic_run_separated(
            "20260722T200000Z-8bba5e01",
            baseline_run_id="20260722T200000Z-8bba5e01",
            diagnostic_root=diag,
            baseline_root=baseline,
        )


@pytest.mark.skipif(not COHORTS.is_file(), reason="cohorts.json missing")
def test_diagnostic_cohort_completeness() -> None:
    suite = load_diagnostic_suite(COHORTS)
    assert validate_diagnostic_suite(suite) == []
    assert suite.not_cobrabench is True
    assert suite.planned_generation_count is not None
    assert suite.planned_generation_count <= 32


def test_controlled_variable_validation() -> None:
    if not COHORTS.is_file():
        pytest.skip("cohorts.json missing")
    suite = load_diagnostic_suite(COHORTS)
    assert suite.cohorts["A_output_cap"].variable == "max_new_tokens"
    assert suite.cohorts["B_thinking"].variable == "enable_thinking"
    assert suite.cohorts["C_prompt_format"].variable == "prompt_variant"
    assert suite.cohorts["D_evidence_delimiters"].variable == "evidence_presentation"
    assert suite.cohorts["E_stability"].variable == "repetition_index"


def test_unsupported_claim_audit_metrics() -> None:
    assert precision(0, 50) == 0.0
    assert false_positive_rate(50, 50) == 1.0


def test_format_failure_classification() -> None:
    assert validate_format_failure_class("syntactic_failure")
    assert not validate_format_failure_class("made_up_label")


def test_human_rescoring_consistency_calculations() -> None:
    pairs = [
        (1.00, 0.95),
        (1.00, 0.95),
        (0.88, 0.86),
        (0.90, 0.88),
        (0.55, 0.50),
        (0.75, 0.72),
        (0.70, 0.68),
        (0.70, 0.65),
    ]
    assert abs(mean_absolute_difference(pairs) - 0.03625) < 1e-9


def test_weakness_matrix_schema_document_exists() -> None:
    text = MATRIX.read_text(encoding="utf-8")
    for wid in ("W01", "W02", "W03", "W04", "W05", "W06", "W07", "W08", "W09"):
        assert wid in text


def test_fix_class_validation() -> None:
    bad = FixProposal(
        weakness_id="W03",
        description="shallow contradiction",
        fix_class=FixClass.MODEL_ADAPTATION_CANDIDATE,
        reproducible=True,
        persists_after_prompt_runtime_controls=None,
        primarily_benchmark_defect=False,
        material_investigation_risk=True,
    )
    assert validate_class4_eligibility(bad)
    good = FixProposal(
        weakness_id="W01",
        description="heuristic noise",
        fix_class=FixClass.EVALUATION_FRAMEWORK,
        primarily_benchmark_defect=True,
    )
    assert validate_class4_eligibility(good) == []


def test_v02_proposal_and_adr_references() -> None:
    adr = ADR4.read_text(encoding="utf-8")
    assert "does not authorize LoRA" in adr
    assert "Class 4 model adaptation" in adr
    assert "Outcome A" in adr and "Outcome B" in adr
    assert "new model acquisition" in adr
    v02 = V02_PROPOSAL.read_text(encoding="utf-8")
    assert "do not modify" in v02.lower()
    assert "v0.1" in v02
    assert STATUS.is_file()
    status = STATUS.read_text(encoding="utf-8")
    assert "Deferred" in status
    assert "0xC0000005" in status


def test_protection_against_overwriting_official_v01_results() -> None:
    import importlib.util

    script = ROOT / "scripts/run_phase2e_diagnostics.py"
    spec = importlib.util.spec_from_file_location("run_phase2e_diagnostics", script)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with pytest.raises(SystemExit):
        mod.main(["--run-id", "20260722T200000Z-8bba5e01", "--dry-run"])


def test_validate_baseline_lock_detects_hash_mismatch(tmp_path: Path) -> None:
    run_dir = tmp_path / "locked-run"
    run_dir.mkdir()
    (run_dir / "run.json").write_text(
        json.dumps({"run_id": "test-run", "cases": []}) + "\n",
        encoding="utf-8",
    )
    lock_path = tmp_path / "baseline-lock.json"
    record = BaselineLockRecord(
        lock_id="test-lock",
        run_id="test-run",
        model_slug="qwen3-8b",
        model_revision="abc123",
        benchmark_version="0.1",
        artifact_inventory_ref="ref",
        benchmark_release_hash="release-hash",
        protocol_path=str(ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.1.json"),
        protocol_hash="deadbeef",
        result_run_path=str(run_dir),
        result_inventory_hash="wrong-hash",
        scoring_implementation_version="v0.1",
        human_review_version="v0.1",
        report_references=[],
        created_at=datetime.now(UTC),
        immutable=True,
    )
    lock_path.write_text(record.model_dump_json(indent=2) + "\n", encoding="utf-8")
    errors = validate_baseline_lock(load_baseline_lock(lock_path), repo_root=ROOT)
    assert any("result_inventory_hash mismatch" in err for err in errors)
