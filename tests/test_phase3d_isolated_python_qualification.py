"""Phase 3D static tests: isolated Python runtime qualification (no model load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.evaluation.rc2_run import RC2_INV, RC2_TREE, inventory_hash, tree_hash

ROOT = Path(__file__).resolve().parents[1]
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
PREPARED = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
COMPAT = ROOT / "evaluations/environments/qwen3-8b-windows-compatibility"
SNAP = ROOT / "evaluations/environments/primary-python313-snapshot"
REQ312 = COMPAT / "requirements-qwen312-lock.txt"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"


def test_frozen_immutability() -> None:
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


def test_primary_snapshot_present() -> None:
    for name in (
        "python-version.txt",
        "python-executable.txt",
        "pip-freeze.txt",
        "pip-check.txt",
        "torch-config.txt",
        "environment-summary.json",
        "cuda-summary.json",
        "bnb-summary.json",
        "sha256sums.txt",
    ):
        assert (SNAP / name).is_file(), name
    exe = (SNAP / "python-executable.txt").read_text(encoding="utf-8")
    assert ".venv" in exe.replace("\\", "/")
    assert "3.13" in (SNAP / "python-version.txt").read_text(encoding="utf-8")


def test_exact_dependency_pinning_no_floating_ranges() -> None:
    text = REQ312.read_text(encoding="utf-8")
    assert "torch" not in text or "torch==" in text or "torch installed separately" in text.lower()
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert ">=" not in s and "~=" not in s and s.count("==") == 1, s


def test_venv_gitignore_and_naming() -> None:
    gi = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".venv-qwen312/" in gi
    assert ".venv-qwen311/" in gi
    assert (COMPAT / "selection-rationale.md").is_file()
    assert (COMPAT / "creation-commands.md").is_file()


def test_model_revision_and_inventory_enforced_in_scripts() -> None:
    worker = (ROOT / "scripts/_qwen312_runtime_worker.py").read_text(encoding="utf-8")
    parent = (ROOT / "scripts/qualify_qwen312_runtime.py").read_text(encoding="utf-8")
    assert MODEL_REV in worker and MODEL_REV in parent
    assert MODEL_INV in worker and MODEL_INV in parent
    assert "CobraBench" not in worker or "not from CobraBench" in parent
    assert "device_map" in worker
    assert '"": 0' in worker or '"": 0' in worker or "{'': 0}" in worker or '{"": 0}' in worker


def test_attempt_budget_constant() -> None:
    parent = (ROOT / "scripts/qualify_qwen312_runtime.py").read_text(encoding="utf-8")
    assert "MAX_FULL_LOADS_312 = 4" in parent
    assert "ACCESS_VIOLATION" in parent


def test_qualification_rule_3_of_3() -> None:
    parent = (ROOT / "scripts/qualify_qwen312_runtime.py").read_text(encoding="utf-8")
    assert "smoke-qualified" in parent
    assert '"required": 3' in parent
    report = (ROOT / "evaluations/reports/QWEN3_8B_ISOLATED_PYTHON_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome D" in report
    assert "0.840" in report


def test_no_benchmark_run_directory_for_rc2() -> None:
    runs = ROOT / "evaluations" / "runs"
    if runs.exists():
        for p in runs.iterdir():
            assert "cobrabench-v0.2-rc2" not in p.name


def test_outcome_and_runtime_candidate_schema_if_present() -> None:
    outcome = ROOT / "evaluations/diagnostics/qwen3-8b-python-runtime-qualification/OUTCOME.json"
    if outcome.is_file():
        data = json.loads(outcome.read_text(encoding="utf-8"))
        assert data["outcome"] in {"A", "B", "C", "D", "E", "F"}
        assert data.get("benchmark_executed") is False
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-windows-isolated-qualified.json"
    if cand.is_file():
        data = json.loads(cand.read_text(encoding="utf-8"))
        assert data["status"] in {
            "qualified",
            "qualified-with-warning",
            "unstable",
            "failed",
        }
        assert data.get("benchmark_authorized") is False
        assert data.get("model_revision") == MODEL_REV


def test_native_library_inventory_schema_if_present() -> None:
    path = COMPAT / "python312" / "native-library-inventory.json"
    if not path.is_file():
        pytest.skip("native inventory not yet written")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert "libraries" in data
    assert "native_library_inventory_hash" in data
    assert isinstance(data["libraries"], list)


@pytest.mark.model_required
def test_live_phase3d_marker_deselected() -> None:
    assert True
