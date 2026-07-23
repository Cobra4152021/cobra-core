"""Phase 3B static tests: rc2 evaluation readiness (no model weight load)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.evaluation.rc2_run import (
    RC2_INV,
    RC2_TREE,
    create_run_workspace,
    finalize_sha256sums,
    inventory_hash,
    make_run_id,
    tree_hash,
)

ROOT = Path(__file__).resolve().parents[1]
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
PREPARED = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"


def test_frozen_hashes_and_baseline_immutable() -> None:
    lock = load_baseline_lock(ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json")
    assert lock.result_inventory_hash == BASELINE_INV
    assert lock.immutable is True
    assert lock.benchmark_version == "0.1"
    report = (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(encoding="utf-8")
    assert "0.840" in report
    rc1 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc1"
    rc2 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
    assert inventory_hash(rc2) == RC2_INV
    assert tree_hash(rc2) == RC2_TREE
    assert inventory_hash(rc1) == "87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87"
    assert tree_hash(rc1) == "3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10"


def test_prepared_protocol_unchanged_status() -> None:
    data = json.loads(PREPARED.read_text(encoding="utf-8"))
    assert data["status"] == "prepared-not-run"
    assert data["benchmark_version"] == "0.2.0-rc2"
    assert "official" not in data["status"]


def test_metric_policy_advisory_and_no_official_rc2() -> None:
    text = (ROOT / "evaluations/policies/qwen3-8b-rc2-metric-interpretation.md").read_text(
        encoding="utf-8"
    )
    assert "advisory-only" in text
    assert "unsupported_claims@2.0.0" in text or "unsupported_claims" in text
    assert "0.840" in text
    assert "pending-human-review" in text
    assert "not available for rc2" in text.lower() or "Official" in text
    assert "not directly comparable" in text.lower() or "Do **not** present" in text


def test_run_id_deterministic_shape() -> None:
    rid = make_run_id()
    assert rid.startswith("qwen3-8b_cobrabench-v0.2-rc2_")
    assert rid.endswith("_4bit-det")


def test_run_directory_schema_and_no_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.ROOT", tmp_path)
    # Point locks/protocol into tmp copies
    rc2_src = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
    rc2_dst = tmp_path / "benchmarks/releases/cobrabench-v0.2-rc2"
    rc2_dst.parent.mkdir(parents=True)
    # Minimal symlink/copy of inventory hashes via real paths is heavy; instead
    # monkeypatch inventory_hash/tree_hash and prepared protocol.
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.RC2_DIR", rc2_src)
    prep = tmp_path / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
    prep.parent.mkdir(parents=True)
    prep.write_text(PREPARED.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.PREPARED_PROTOCOL", prep)
    baseline = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.BASELINE_LOCK", baseline)

    preflight = {"pass_fail_status": "pass", "warnings": []}
    inventory = {"inventory_hash": "abc"}
    run_id = "qwen3-8b_cobrabench-v0.2-rc2_test_4bit-det"
    run_dir = create_run_workspace(
        run_id, code_commit="deadbeef", preflight=preflight, inventory=inventory
    )
    for name in (
        "protocol.json",
        "environment.json",
        "model_inventory.json",
        "RUN.md",
        "raw",
        "parsed",
        "telemetry",
        "scores",
        "human_review",
        "logs",
        "errors",
        "reports",
    ):
        assert (run_dir / name).exists()
    protocol = json.loads((run_dir / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "running"
    assert protocol["model_inventory_hash"] == "abc"
    assert protocol["rc2_inventory_hash"] == RC2_INV
    assert json.loads(prep.read_text(encoding="utf-8"))["status"] == "prepared-not-run"
    with pytest.raises(RuntimeError, match="already exists"):
        create_run_workspace(
            run_id, code_commit="deadbeef", preflight=preflight, inventory=inventory
        )


def test_deterministic_case_order_helper() -> None:
    from cobra_core.benchmarks.release import load_release_cases_v02

    cases = load_release_cases_v02("0.2.0-rc2")
    ids = [c.case_id for c in cases]
    assert ids == sorted(ids)
    assert len(ids) == 46


def test_preflight_and_inventory_artifacts_exist() -> None:
    pre = ROOT / "evaluations/preflight/qwen3-8b-v0.2-rc2-preflight.json"
    inv = ROOT / "evaluations/model-inventory/qwen3-8b-local-inventory.json"
    assert pre.is_file()
    assert inv.is_file()
    pdata = json.loads(pre.read_text(encoding="utf-8"))
    idata = json.loads(inv.read_text(encoding="utf-8"))
    assert pdata["pass_fail_status"] in {"pass", "warn"}
    assert idata["model_revision"] == "b968826d9c46dd6066d109eabc6255188de91218"
    assert "inventory_hash" in idata
    assert "Dynamic Mining" not in json.dumps(idata)


def test_no_official_label_helpers() -> None:
    from cobra_core.benchmarks.release import load_release_cases_v02
    from cobra_core.evaluation.rc2_run import build_human_review_queue

    case = load_release_cases_v02("0.2.0-rc2")[0]
    items = build_human_review_queue(case, {"advisory": {}, "authoritative": {}}, "raw/x.txt")
    for item in items:
        assert item["reviewer_status"] == "pending-human-review"


def test_sha256sums_generation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.ROOT", tmp_path)
    monkeypatch.setattr(
        "cobra_core.evaluation.rc2_run.RC2_DIR",
        ROOT / "benchmarks/releases/cobrabench-v0.2-rc2",
    )
    prep = tmp_path / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"
    prep.parent.mkdir(parents=True)
    prep.write_text(PREPARED.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr("cobra_core.evaluation.rc2_run.PREPARED_PROTOCOL", prep)
    monkeypatch.setattr(
        "cobra_core.evaluation.rc2_run.BASELINE_LOCK",
        ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json",
    )
    run_dir = create_run_workspace(
        "qwen3-8b_cobrabench-v0.2-rc2_sha_4bit-det",
        code_commit="deadbeef",
        preflight={"ok": True},
        inventory={"inventory_hash": "xyz"},
    )
    (run_dir / "raw" / "CASE.txt").write_text("preserved raw\n", encoding="utf-8")
    digest = finalize_sha256sums(run_dir)
    sums = (run_dir / "SHA256SUMS").read_text(encoding="utf-8")
    assert "raw/CASE.txt" in sums
    assert len(digest) == 64


def test_smoke_failure_blocks_benchmark_claim() -> None:
    smoke = json.loads(
        (ROOT / "evaluations/smoke/qwen3-8b-rc2-readiness/smoke_result.json").read_text(
            encoding="utf-8"
        )
    )
    assert smoke["status"] == "fail"
    assert smoke["benchmark_execution"] == "blocked"
    assert smoke["windows_exit_code_hex"] == "0xC0000005"
    summary = (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_2_RC2_SUMMARY.md").read_text(
        encoding="utf-8"
    )
    assert "0.840" in summary
    assert "not reported" in summary.lower() or "not reported" in summary
    assert "official" in summary.lower()
    adr = (ROOT / "docs/decisions/ADR-0010-qwen3-8b-rc2-experimental-evaluation.md").read_text(
        encoding="utf-8"
    )
    assert "does not supersede the official CobraBench v0.1 score of 0.840" in adr
    assert "Gate 3" in adr


@pytest.mark.model_required
def test_live_smoke_marker_deselected_by_default() -> None:
    """Live weight-loading tests must be explicitly selected."""
    assert True
