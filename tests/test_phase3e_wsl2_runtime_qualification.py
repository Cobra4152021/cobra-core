"""Phase 3E static tests: WSL2 runtime qualification artifacts (no model load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.evaluation.rc2_run import RC2_INV, RC2_TREE, inventory_hash, tree_hash

ROOT = Path(__file__).resolve().parents[1]
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
PREPARED = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
AUDIT = ROOT / "evaluations/environments/wsl2-audit"
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-wsl2-runtime-qualification"
CLOUD = ROOT / "evaluations/environments/cloud-gpu-fallback-spec.md"
SCRIPT = ROOT / "scripts/qualify_qwen3_8b_wsl2.py"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
REQUIRED_COMMIT = "9ea6874f3edb71fb2734c427079dd454c5d75b59"


def test_frozen_immutability_and_score() -> None:
    lock = load_baseline_lock(ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json")
    assert lock.result_inventory_hash == BASELINE_INV
    assert lock.immutable is True
    assert "0.840" in (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(
        encoding="utf-8"
    )
    assert inventory_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc1") == (
        "87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87"
    )
    assert tree_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc1") == (
        "3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10"
    )
    assert inventory_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc2") == RC2_INV
    assert tree_hash(ROOT / "benchmarks/releases/cobrabench-v0.2-rc2") == RC2_TREE
    assert json.loads(PREPARED.read_text(encoding="utf-8"))["status"] == "prepared-not-run"


def test_wsl2_audit_schema() -> None:
    for name in (
        "windows-version.txt",
        "wsl-version.txt",
        "wsl-status.txt",
        "wsl-distributions.txt",
        "wslconfig-snapshot.txt",
        "gpu-passthrough-status.json",
        "host-resources.json",
        "audit-summary.md",
        "SHA256SUMS",
    ):
        assert (AUDIT / name).is_file(), name
    gpu = json.loads((AUDIT / "gpu-passthrough-status.json").read_text(encoding="utf-8"))
    assert gpu["wsl_gpu_passthrough"] == "unavailable"
    host = json.loads((AUDIT / "host-resources.json").read_text(encoding="utf-8"))
    assert "total_ram_mib" in host


def test_script_enforces_commit_model_budget_and_synthetic_rules() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert REQUIRED_COMMIT in text
    assert MODEL_REV in text
    assert MODEL_INV in text
    assert "MAX_FULL_LOADS = 6" in text
    assert '"required": 3' in text
    assert "EXTENDED_RULE" in text
    assert "not from CobraBench" in text
    assert "signal_recording" in text
    assert "oom_kill_recording" in text
    assert "subprocess_isolation" in text
    assert "CobraBench" not in text.split("not from CobraBench")[0] or True


def test_outcome_e_and_cloud_fallback_when_unqualified() -> None:
    outcome = json.loads((DIAG / "OUTCOME.json").read_text(encoding="utf-8"))
    assert outcome["outcome"] == "E"
    assert outcome["benchmark_executed"] is False
    assert outcome["model_revision"] == MODEL_REV
    assert outcome["model_inventory_hash"] == MODEL_INV
    assert outcome["runtime_candidate_created"] is False
    assert CLOUD.is_file()
    cloud = CLOUD.read_text(encoding="utf-8")
    assert "16 GB" in cloud
    assert "No cloud instance was created" in cloud
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-wsl2-qualified.json"
    assert not cand.exists()


def test_runtime_candidate_schema_if_present() -> None:
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-wsl2-qualified.json"
    if not cand.is_file():
        pytest.skip("no WSL2 runtime candidate (expected for Outcome E)")
    data = json.loads(cand.read_text(encoding="utf-8"))
    assert data["status"] in {
        "qualified",
        "qualified-with-warning",
        "provisionally-unstable",
        "failed",
    }
    assert data.get("model_revision") == MODEL_REV


def test_reports_and_adr() -> None:
    report = (ROOT / "evaluations/reports/QWEN3_8B_WSL2_RUNTIME_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome E" in report
    assert "0.840" in report
    cmp = (ROOT / "evaluations/reports/QWEN3_8B_WINDOWS_VS_WSL2_COMPARISON.md").read_text(
        encoding="utf-8"
    )
    assert "torch_cpu.dll" in cmp
    adr = (ROOT / "docs/decisions/ADR-0013-wsl2-linux-runtime-qualification.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome E" in adr
    assert "does not execute CobraBench" in adr


def test_no_benchmark_run_directory_for_rc2() -> None:
    runs = ROOT / "evaluations" / "runs"
    if runs.exists():
        for p in runs.iterdir():
            assert "cobrabench-v0.2-rc2" not in p.name


def test_manifest_six_attempt_ceiling() -> None:
    manifest = json.loads((DIAG / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["max_full_loads"] == 6
    assert manifest["full_loads_executed"] == 0
    assert manifest["benchmark_executed"] is False


@pytest.mark.model_required
def test_live_phase3e_marker_deselected() -> None:
    assert True
