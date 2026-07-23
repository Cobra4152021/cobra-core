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
    assert auth["authorized"] is True
    assert auth["provider"] == "RunPod"
    assert auth["gpu"] == "NVIDIA L4"
    assert float(auth["approved_spending_ceiling_usd"]) == 10.0
    assert float(auth["approved_runtime_ceiling_hours"]) == 8
    assert float(auth["quoted_hourly_rate_usd"]) <= 0.5
    assert auth["rules"]["max_active_gpu_instances"] == 1
    assert auth["spot_or_interruptible"] is False
    assert auth["payment_information_recorded"] is False
    block = json.loads((CLOUD / "provisioning-block.json").read_text(encoding="utf-8"))
    assert block["price_precheck"]["within_limit"] is True
    # Either still waiting on credentials, or adopted with a later connection block.
    cred = json.loads((CLOUD / "credential-status.json").read_text(encoding="utf-8"))
    assert "credential_present" in cred
    assert "authentication_succeeded" in cred
    assert cred["credential_source"] in {"none", "environment variable"}
    conn = CLOUD / "connection-block.json"
    if conn.is_file():
        cb = json.loads(conn.read_text(encoding="utf-8"))
        assert cb["block_class"] in {"remote_access", "resolved"}
        assert cb.get("create_new_pod") is False
        assert "pod_id" in cb


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
    assert isinstance(data["ports_opened"], list)
    assert "22/tcp" in data["ports_opened"] or data["ports_opened"] == []
    assert data["secrets_used_by_category"] == []
    assert data.get("public_inference_endpoint") is not True
    assert "BEGIN RSA PRIVATE KEY" not in text
    assert "sk-" not in text
    # Values must not look like credentials; keys may mention auth categories.
    for key, value in data.items():
        if key in {"prohibited", "cleanup_requirements", "schema", "status", "notes"}:
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


def test_outcome_a_qualified_cost_cleanup() -> None:
    outcome = json.loads((DIAG / "OUTCOME.json").read_text(encoding="utf-8"))
    assert outcome["outcome"] == "A"
    assert outcome["authorized"] is True
    assert outcome["benchmark_executed"] is False
    assert outcome["qualification_passed"] is True
    assert outcome["extended_passed"] is True
    assert outcome["create_new_pod"] is False
    assert outcome["runtime_candidate_created"] is True
    assert float(outcome["official_v01_score_unchanged"]) == 0.84
    cost = json.loads((CLOUD / "cost-record.json").read_text(encoding="utf-8"))
    assert cost["ceiling_respected"] is True
    assert float(cost["approved_spending_ceiling_usd"]) == 10.0
    assert float(cost["total_estimated_cost_usd"]) <= 10.0
    cleanup = json.loads((CLOUD / "cleanup-verification.json").read_text(encoding="utf-8"))
    assert cleanup["instance_terminated"] is True
    assert cleanup["remaining_billable_resources"] == []
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json"
    assert cand.is_file()


def test_runtime_candidate_schema_if_present() -> None:
    cand = ROOT / "evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json"
    if not cand.is_file():
        pytest.skip("no cloud runtime candidate")
    data = json.loads(cand.read_text(encoding="utf-8"))
    assert data["status"] in {
        "qualified",
        "qualified-with-warning",
        "provisionally-unstable",
        "failed",
    }
    assert data.get("model_revision") == MODEL_REV
    assert data.get("qualification_3_of_3") is True
    assert data.get("extended_session") is True
    assert data.get("benchmark_executed") is False


def test_reports_and_adr() -> None:
    report = (ROOT / "evaluations/reports/QWEN3_8B_CLOUD_LINUX_RUNTIME_QUALIFICATION.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome" in report
    assert "RunPod" in report
    assert "0.840" in report
    assert "A — Cloud Linux runtime fully qualified" in report
    cmp = (ROOT / "evaluations/reports/QWEN3_8B_PLATFORM_COMPARISON.md").read_text(encoding="utf-8")
    assert "WSL2" in cmp
    assert "A" in cmp
    adr = (ROOT / "docs/decisions/ADR-0014-cloud-linux-runtime-qualification.md").read_text(
        encoding="utf-8"
    )
    assert "Outcome A" in adr
    assert "does not execute CobraBench" in adr


def test_no_benchmark_run_directory_for_rc2() -> None:
    runs = ROOT / "evaluations" / "runs"
    if runs.exists():
        for p in runs.iterdir():
            assert "cobrabench-v0.2-rc2" not in p.name


def test_manifest_six_load_ceiling() -> None:
    manifest = json.loads((DIAG / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["max_full_loads"] == 6
    assert manifest["full_loads_executed"] == 6
    assert manifest["benchmark_executed"] is False


@pytest.mark.model_required
def test_live_phase3f_marker_deselected() -> None:
    assert True
