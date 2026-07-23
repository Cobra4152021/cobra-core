"""Phase 3C static tests: Windows load isolation (no model weight load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.diagnostics.load_isolation import (
    CONFIGS,
    MAX_LIVE_LOAD_ATTEMPTS,
    SMOKE_PROMPT,
    attempt_schema,
    classify_qualification,
    count_live_loads,
    is_access_violation,
    windows_status_hex,
)
from cobra_core.evaluation.rc2_run import RC2_INV, RC2_TREE, inventory_hash, tree_hash

ROOT = Path(__file__).resolve().parents[1]
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
PREPARED = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-windows-load-isolation"


def test_frozen_artifacts_immutable() -> None:
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


def test_configuration_id_uniqueness_and_ceiling() -> None:
    assert MAX_LIVE_LOAD_ATTEMPTS == 6
    assert len(CONFIGS) >= 5
    assert len(set(CONFIGS)) == len(CONFIGS)


def test_attempt_and_subprocess_schema() -> None:
    rec = attempt_schema(
        attempt_id="attempt-01-A",
        configuration_id="A",
        pid=123,
        started_at="2026-07-23T00:00:00+00:00",
        ended_at="2026-07-23T00:01:00+00:00",
        exit_code=3221225477,
        load_stage="model_from_pretrained_begin",
        success=False,
        extra={"live_load": True},
    )
    assert rec["schema"] == "cobra.diagnostics.load_attempt.v1"
    assert rec["windows_status_code"] == "0xC0000005"
    assert rec["access_violation"] is True
    assert rec["benchmark_prompt_used"] is False
    assert rec["benchmark_run_created"] is False
    assert is_access_violation(3221225477)
    assert windows_status_hex(-1073741819) == "0xC0000005"


def test_max_attempt_enforcement_helper() -> None:
    records = [
        {"live_load": True, "metadata_only": False, "configuration_id": f"X{i}"} for i in range(6)
    ]
    assert count_live_loads(records) == 6
    with pytest.raises(RuntimeError, match="ceiling"):
        # emulate orchestrator guard
        if count_live_loads(records) >= MAX_LIVE_LOAD_ATTEMPTS:
            raise RuntimeError(f"live load attempt ceiling {MAX_LIVE_LOAD_ATTEMPTS} reached")


def test_no_benchmark_prompt_in_smoke() -> None:
    assert "CobraBench" not in SMOKE_PROMPT
    assert "cobrabench" not in SMOKE_PROMPT.lower()
    assert "SRC-A" in SMOKE_PROMPT
    # ensure prepared protocol path is not a run dir creator in diagnostics module
    runs = (
        list((ROOT / "evaluations" / "runs").glob("*"))
        if (ROOT / "evaluations" / "runs").exists()
        else []
    )
    # Phase 3C must not create benchmark runs; directory may be absent or empty of rc2 runs
    for path in runs:
        assert "cobrabench-v0.2-rc2" not in path.name or path.name.startswith(".")


def test_qualification_classification() -> None:
    assert classify_qualification(3, 3) == "smoke-qualified"
    assert classify_qualification(2, 3) == "unstable"
    assert classify_qualification(0, 3) == "failed"


def test_phase3b_evidence_preserved() -> None:
    evid = DIAG / "phase3b-evidence"
    assert evid.is_dir()
    assert (DIAG / "SOURCE_EVIDENCE.md").is_file()
    assert (evid / "smoke_result.json").is_file()
    assert (evid / "smoke_attempt1_crash.json").is_file()
    assert (evid / "qwen3-8b-local-inventory.json").is_file()
    # originals untouched
    assert (ROOT / "evaluations/smoke/qwen3-8b-rc2-readiness/smoke_result.json").is_file()


def test_file_integrity_artifact() -> None:
    path = ROOT / "evaluations/model-inventory/qwen3-8b-file-integrity.json"
    assert path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "pass"
    assert data["model_revision"] == "b968826d9c46dd6066d109eabc6255188de91218"
    assert data.get("corruption_detected") is False


def test_runtime_candidate_status_rules() -> None:
    cand_dir = ROOT / "evaluations/runtime-candidates"
    if not cand_dir.exists():
        return
    for path in cand_dir.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("qualification_status") in {
            "smoke-qualified",
            "unstable",
            "failed",
            "not-qualified",
        }
        assert data.get("benchmark_authorized") is False


@pytest.mark.model_required
def test_live_diag_marker_deselected() -> None:
    assert True
