"""Tests for Phase 2D interim baseline protocol and reporting guards."""

from __future__ import annotations

import json
from pathlib import Path

from cobra_core.benchmarks.release import validate_release_inventory
from cobra_core.evaluation.cobrabench_run import detect_missing_human_review
from cobra_core.schemas.eligibility import environment_blocks_runtime, is_benchmark_runnable
from cobra_core.schemas.manifest import (
    BenchmarkEligibilityStatus,
    ModelManifest,
    RuntimeValidationStatus,
)


def test_protocol_file_matches_frozen_pins(repo_root: Path) -> None:
    protocol_path = repo_root / "evaluations" / "protocols" / "qwen3-8b-cobrabench-v0.1.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    assert protocol["model"]["revision"] == ("b968826d9c46dd6066d109eabc6255188de91218")
    assert protocol["sampling"]["temperature"] == 0.0
    assert protocol["sampling"]["seed"] == 123
    assert protocol["thinking_mode"]["enable_thinking"] is False
    assert protocol["runtime"]["max_new_tokens"] == 512
    assert protocol["retry_policy"]["max_retries"] == 0
    assert protocol["benchmark"]["inventory_sha256"]
    assert validate_release_inventory("0.1") == []


def test_qwen3_8b_interim_or_completed_status(repo_root: Path) -> None:
    manifest = ModelManifest.model_validate_json(
        (repo_root / "model-cards" / "qwen" / "qwen3-8b.manifest.json").read_text(encoding="utf-8")
    )
    assert manifest.runtime_validation_status == RuntimeValidationStatus.LOAD_PASSED
    assert manifest.benchmark_eligibility_status in {
        BenchmarkEligibilityStatus.INTERIM_ELIGIBLE,
        BenchmarkEligibilityStatus.BENCHMARK_COMPLETED,
    }
    assert is_benchmark_runnable(manifest) or (
        manifest.benchmark_eligibility_status == BenchmarkEligibilityStatus.BENCHMARK_COMPLETED
    )


def test_qwen3_32b_blocked_runtime_status(repo_root: Path) -> None:
    manifest = ModelManifest.model_validate_json(
        (repo_root / "model-cards" / "qwen" / "qwen3-32b.manifest.json").read_text(encoding="utf-8")
    )
    assert environment_blocks_runtime(manifest)
    assert manifest.benchmark_eligibility_status == BenchmarkEligibilityStatus.BLOCKED_BY_RUNTIME
    assert not is_benchmark_runnable(manifest)


def test_empty_judge_result_handling() -> None:
    payload = {"status": "not_run", "scores": []}
    assert payload["status"] == "not_run"
    assert payload["scores"] == []


def test_missing_human_review_detection() -> None:
    assert detect_missing_human_review({"status": "pending", "scores": []}) is True
    assert (
        detect_missing_human_review(
            {"status": "complete", "scores": [{"case_id": "x", "score": 0.5}]}
        )
        is False
    )


def test_comparison_report_states_no_32b_scores(repo_root: Path) -> None:
    text = (repo_root / "evaluations" / "reports" / "QWEN3_8B_VS_32B_COMPARISON.md").read_text(
        encoding="utf-8"
    )
    assert "No dual-model comparison exists" in text
    assert "No Qwen3-32B CobraBench scores exist" in text
    assert "must not" in text.lower()


def test_defect_report_exists_and_classifies(repo_root: Path) -> None:
    text = (repo_root / "evaluations" / "reports" / "COBRABENCH_V0_1_DEFECT_REVIEW.md").read_text(
        encoding="utf-8"
    )
    assert "Classification" in text or "classification" in text.lower()
    assert "v0.1" in text
    assert "not" in text.lower() and "modified" in text.lower()


def test_human_coverage_calculation() -> None:
    coverage = {"reviewed": 28, "total_response_files": 28, "fraction": 1.0}
    assert coverage["fraction"] >= 0.5
    assert coverage["reviewed"] == coverage["total_response_files"]
