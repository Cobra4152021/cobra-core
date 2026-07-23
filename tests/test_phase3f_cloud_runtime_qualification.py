"""Phase 3F static tests: cloud Linux qualification prep (no provision, no model load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.evaluation.rc2_run import RC2_INV, RC2_TREE, inventory_hash, tree_hash

ROOT = Path(__file__).resolve().parents[1]
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
PREPARED = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
CLOUD = ROOT / "evaluations/cloud"
ENV = ROOT / "evaluations/environments/cloud-qwen3-runtime"
DIAG = ROOT / "evaluations/diagnostics/qwen3-8b-cloud-runtime-qualification"
SCRIPT = ROOT / "scripts/qualify_qwen3_8b_cloud.py"
LOCK = ENV / "requirements-cloud-lock.txt"
MODEL_REV = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_INV = "8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f"
REQUIRED_COMMIT = "695ea8833229b183e5792c49e3888ec4dde9e5f2"


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


def test_authorization_schema_and_single_instance_rule() -> None:
    auth = json.loads((CLOUD / "authorization-record.json").read_text(encoding="utf-8"))
    assert auth["schema"] == "cobra.cloud.authorization.v1"
    assert auth["authorized"] is False
    assert auth["status"] == "ready-for-cloud-authorization"
    assert auth["rules"]["max_active_gpu_instances"] == 1
    assert auth["payment_information_recorded"] is False
    assert auth["provider"] is None


def test_transfer_manifest_schema() -> None:
    manifest = json.loads((CLOUD / "cloud-transfer-manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "cobra.cloud.transfer_manifest.v1"
    assert manifest["source_commit"] == REQUIRED_COMMIT
    assert manifest["model_weights_included"] is False
    assert manifest["model_revision"] == MODEL_REV
    assert manifest["model_inventory_hash"] == MODEL_INV
    assert "included" in manifest and "excluded" in manifest
    assert manifest["total_bundle_size_bytes"] >= 0


def test_security_manifest_has_no_secret_fields() -> None:
    text = (CLOUD / "security-manifest.json").read_text(encoding="utf-8")
    data = json.loads(text)
    assert data["contains_secrets"] is False
    assert data["ports_opened"] == []
    assert data["secrets_used_by_category"] == []
    assert "BEGIN RSA PRIVATE KEY" not in text
    assert "sk-" not in text
    # Values must not look like credentials; keys may mention auth categories.
    for key, value in data.items():
        if key in {"prohibited", "cleanup_requirements", "schema", "status"}:
            continue
        if isinstance(value, str):
            assert "BEGIN " not in value
            assert not value.startswith("sk-")


def test_exact_dependency_pins() -> None:
    text = LOCK.read_text(encoding="utf-8")
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        assert ">=" not in s and "~=" not in s
        assert s.count("==") == 1, s


def test_script_enforces_commit_model_budget_and_gates() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert REQUIRED_COMMIT in text
    assert MODEL_REV in text
    assert MODEL_INV in text
    assert "MAX_FULL_LOADS = 6" in text
    assert '"required": 3' in text
    assert "EXTENDED_RULE" in text
    assert "not from CobraBench" in text
    assert "spending_ceiling_enforced" in text
    assert "single_instance_rule" in text
    assert "signal_recording" in text
    assert "oom_kill_recording" in text
    assert "subprocess_isolation" in text
    assert "COBRA_CLOUD_PROVISION" in text


def test_outcome_h_cost_cleanup_export() -> None:
    outcome = json.loads((DIAG / "OUTCOME.json").read_text(encoding="utf-8"))
    assert outcome["outcome"] == "H"
    assert outcome["status"] == "ready-for-cloud-authorization"
    assert outcome["instance_count"] == 0
    assert outcome["benchmark_executed"] is False
    assert outcome["total_estimated_cost_usd"] == 0
    cost = json.loads((CLOUD / "cost-record.json").read_text(encoding="utf-8"))
    assert cost["ceiling_respected"] is True
    assert cost["total_estimated_cost_usd"] == 0
    cleanup = json.loads((CLOUD / "cleanup-verification.json").read_text(encoding="utf-8"))
    assert cleanup["remaining_billable_resources"] == []
    export = json.loads((CLOUD / "export-verification.json").read_text(encoding="utf-8"))
    assert export["verification_status"] == "local_preparation_complete"
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json"
    assert not cand.exists()


def test_runtime_candidate_schema_if_present() -> None:
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json"
    if not cand.is_file():
        pytest.skip("no cloud runtime candidate (expected for Outcome H)")
    data = json.loads(cand.read_text(encoding="utf-8"))
    assert data["status"] in {
        "qualified",
        "qualified-with-warning",
        "provisionally-unstable",
        "failed",
    }
    assert data.get("model_revision") == MODEL_REV


def test_reports_and_adr() -> None:
    report = (ROOT / "evaluations/reports/QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome" in report and "H" in report
    assert "0.840" in report
    cmp = (ROOT / "evaluations/reports/QWEN3_8B_PLATFORM_COMPARISON.md").read_text(encoding="utf-8")
    assert "WSL2" in cmp
    adr = (ROOT / "docs/decisions/ADR-0014-cloud-linux-runtime-qualification.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome H" in adr
    assert "does not execute CobraBench" in adr


def test_no_benchmark_run_directory_for_rc2() -> None:
    runs = ROOT / "evaluations" / "runs"
    if runs.exists():
        for p in runs.iterdir():
            assert "cobrabench-v0.2-rc2" not in p.name


def test_manifest_six_load_ceiling() -> None:
    manifest = json.loads((DIAG / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["max_full_loads"] == 6
    assert manifest["full_loads_executed"] == 0


@pytest.mark.model_required
def test_live_phase3f_marker_deselected() -> None:
    assert True
