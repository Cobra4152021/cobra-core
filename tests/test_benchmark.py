"""KC-030 Investigation Evaluation & Benchmark Framework tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.benchmark.audit import BENCHMARK_AUDIT
from cobra_core.benchmark.config import BenchmarkConfig, load_benchmark_config
from cobra_core.benchmark.dataset import dataset_from_dict, validate_dataset
from cobra_core.benchmark.datasets.builtin import BUILTIN_DATASETS, register_builtin_datasets
from cobra_core.benchmark.engine import BenchmarkEngine
from cobra_core.benchmark.metrics import BENCHMARK_METRICS, BenchmarkMetrics
from cobra_core.benchmark.registry import DatasetRegistry
from cobra_core.benchmark.report import render_html, render_json, render_markdown, write_reports
from cobra_core.benchmark.runner import BenchmarkRunner, mock_executor
from cobra_core.benchmark.schemas import BenchmarkExecution
from cobra_core.benchmark.scoring import (
    confidence_calibration_score,
    finding_scores,
    score_case,
    score_citations,
)
from cobra_core.isf.schemas import empty_skill_output


@pytest.fixture(autouse=True)
def _isolate_metrics():
    BENCHMARK_METRICS.clear()
    BENCHMARK_AUDIT.clear()
    yield
    BENCHMARK_METRICS.clear()
    BENCHMARK_AUDIT.clear()


def test_builtin_datasets_validate():
    reg = DatasetRegistry()
    register_builtin_datasets(reg)
    ids = reg.list_ids()
    assert "vehicle_damage_v1" in ids
    assert "policy_review_v1" in ids
    assert "contract_analysis_v1" in ids
    assert "budget_analysis_v1" in ids
    assert "timeline_v1" in ids
    assert "evidence_summary_v1" in ids
    assert "document_comparison_v1" in ids
    for ds in BUILTIN_DATASETS:
        assert validate_dataset(ds) == []


def test_dataset_from_dict_and_versioning():
    raw = {
        "dataset_id": "toy_v1",
        "version": "1.2.0",
        "skill_id": "policy_compliance_review",
        "title": "Toy",
        "cases": [
            {
                "case_id": "t1",
                "skill_id": "policy_compliance_review",
                "task": "review",
                "evidence": [{"evidence_type": "policy_document", "ref_id": "p1"}],
                "gold": {
                    "findings": ["a"],
                    "citations": ["EV-001"],
                    "confidence_min": 0.2,
                    "confidence_max": 0.6,
                },
            }
        ],
    }
    ds = dataset_from_dict(raw)
    assert ds.version == "1.2.0"
    assert ds.cases[0].dataset_version == "1.2.0"


def test_finding_and_citation_scoring():
    f1, fpr, fnr = finding_scores(["front bumper damage"], ["front bumper damage", "hood crease"])
    assert f1 < 1.0
    assert fnr > 0
    cite = score_citations(["EV-001", "EV-001", "EV-999"], ("EV-001", "EV-002"))
    assert cite.supported == 1
    assert cite.incorrect == 1
    assert cite.missing == 1
    assert cite.duplicate == 1


def test_confidence_calibration():
    from cobra_core.benchmark.schemas import GoldStandard

    gold = GoldStandard(confidence_min=0.3, confidence_max=0.55)
    high_wrong = confidence_calibration_score(0.9, gold, findings_correct=False)
    high_right = confidence_calibration_score(0.9, gold, findings_correct=True)
    assert high_wrong < high_right


def test_mock_runner_passes_builtin_dataset():
    runner = BenchmarkRunner()
    result = runner.run_dataset("policy_review_v1", provider_id="mock", repeats=1)
    assert result.passed
    assert result.overall_score >= 0.7
    assert result.provider_id == "mock"
    assert result.case_scores


def test_repeatability_identical_mock():
    runner = BenchmarkRunner()
    result = runner.run_dataset("budget_analysis_v1", repeats=3)
    assert result.repeatability
    assert result.repeatability[0].identical_output_rate == 1.0
    assert result.repeatability[0].citation_variance == 0.0


def test_provider_comparison_labels_only():
    runner = BenchmarkRunner()
    compared = runner.compare_providers(
        "evidence_summary_v1", ["mock", "openai"], workflow_id="isf_default"
    )
    assert set(compared) == {"mock", "openai"}
    # Same mock executor → equal scores; routing unchanged (label only).
    assert compared["mock"].overall_score == compared["openai"].overall_score


def test_reports_json_md_html(tmp_path: Path):
    runner = BenchmarkRunner()
    result = runner.run_dataset("timeline_v1")
    js = render_json(result)
    md = render_markdown(result)
    ht = render_html(result)
    assert '"overall_score"' in js
    assert "Benchmark Report" in md
    assert "<html" in ht
    paths = write_reports(result, tmp_path)
    assert paths["json"].is_file()
    assert paths["markdown"].is_file()
    assert paths["html"].is_file()


def test_metrics_and_audit_isolated():
    metrics = BenchmarkMetrics()
    metrics.record_run(
        passed=True,
        overall_score=0.9,
        latency_avg_ms=10.0,
        cost_total_usd=0.0,
        repeatability_rate=1.0,
    )
    snap = metrics.snapshot()
    assert snap["benchmark_runs"] == 1
    assert snap["benchmark_pass"] == 1
    assert "benchmark_accuracy" in snap
    prom = metrics.render_prometheus()
    assert "benchmark_runs 1" in prom

    runner = BenchmarkRunner()
    runner.run_dataset("contract_analysis_v1")
    entries = BENCHMARK_AUDIT.recent(limit=5)
    assert entries
    assert entries[0]["channel"] == "benchmark_isolated"
    blob = json.dumps(entries)
    assert "api_key" not in blob.lower() or "[redacted]" in blob


def test_score_case_missing_evidence_path():
    from cobra_core.benchmark.datasets.builtin import BUILTIN_DATASETS

    ds = next(d for d in BUILTIN_DATASETS if d.dataset_id == "vehicle_damage_v1")
    case = next(c for c in ds.cases if c.gold.expect_missing_evidence)
    ex = BenchmarkExecution(
        case_id=case.case_id,
        skill_id=case.skill_id,
        provider_id="mock",
        workflow_id="isf_default",
        output={},
        error_code="missing_required_evidence",
    )
    sc = score_case(case, ex, BenchmarkConfig())
    assert sc.passed
    assert sc.overall == 1.0


def test_regression_bad_citations_lowers_score():
    from cobra_core.benchmark.datasets.builtin import BUILTIN_DATASETS

    ds = next(d for d in BUILTIN_DATASETS if d.dataset_id == "policy_review_v1")
    case = ds.cases[0]
    bad = empty_skill_output(
        case.skill_id,
        summary="policy coverage",
        confidence=0.45,
        findings=list(case.gold.findings),
        citations=["EV-FAKE"],
        compliance_status="partial",
    )
    ex = BenchmarkExecution(
        case_id=case.case_id,
        skill_id=case.skill_id,
        provider_id="mock",
        workflow_id="w",
        output=bad,
    )
    good_raw = mock_executor(case, "mock")
    good = BenchmarkExecution(
        case_id=case.case_id,
        skill_id=case.skill_id,
        provider_id="mock",
        workflow_id="w",
        output=good_raw["output"],
    )
    cfg = BenchmarkConfig()
    assert score_case(case, good, cfg).overall > score_case(case, ex, cfg).overall


def test_config_load_and_engine_disabled():
    cfg = load_benchmark_config({"BENCHMARK_ENABLED": "false"})
    assert cfg.enabled is False
    engine = BenchmarkEngine(config=cfg)
    with pytest.raises(RuntimeError):
        engine.score_executions(BUILTIN_DATASETS[0], [])
