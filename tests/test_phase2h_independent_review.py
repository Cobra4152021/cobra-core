"""Phase 2H independent review and rc2 gating tests (no model load)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.benchmarks.release import (
    load_release_cases,
    load_release_cases_v02,
    validate_release_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
RC1 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc1"
RC2 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
FINAL = ROOT / "benchmarks/releases/cobrabench-v0.2"
REVIEW = ROOT / "evaluations/reviews/cobrabench-v0.2-rc1-independent-review"
SENS = ROOT / "evaluations/fixtures/cobrabench-v0.2-rc2-scoring-sensitivity"
BASELINE_LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
RC1_PROTOCOL = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc1.json"
RC2_PROTOCOL = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"

RC1_TREE = "3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10"
RC1_INV = "87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87"
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"

VALID_STATUSES = {
    "approve_unchanged",
    "approve_with_documentation_note",
    "revise_before_final",
    "remove",
    "unresolved",
}
VALID_SEVERITIES = {"D0", "D1", "D2", "D3", "D4"}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path) -> str:
    entries: list[str] = []
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()
    ):
        if path.is_file() and path.name not in {"TREE_HASH.txt", "SHA256SUMS"}:
            rel = path.relative_to(root).as_posix()
            entries.append(f"{rel}:{_sha256_file(path)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def _inventory_hash(root: Path) -> str:
    inv = json.loads((root / "INVENTORY.json").read_text(encoding="utf-8"))
    payload = "\n".join(f"{e['filename']}:{e['sha256']}" for e in inv["cases"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_rc1_immutability_hashes() -> None:
    assert validate_release_inventory("0.2.0-rc1") == []
    assert (RC1 / "TREE_HASH.txt").read_text(encoding="utf-8").strip() == RC1_TREE
    assert _tree_hash(RC1) == RC1_TREE
    assert _inventory_hash(RC1) == RC1_INV


def test_independent_review_record_completeness() -> None:
    summary = json.loads((REVIEW / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["case_count"] == 46
    assert summary["multi_rater"] is False
    assert summary["saw_original_approval_notes"] is False
    assert summary["release_outcome"] == "B_create_rc2"
    assert len(summary["reviews"]) == 46
    statuses = {r["status"] for r in summary["reviews"]}
    assert statuses <= VALID_STATUSES
    assert all(r["status"] != "unresolved" for r in summary["reviews"])
    assert all(not r.get("unresolved_ambiguity") for r in summary["reviews"])
    case_files = sorted((REVIEW / "cases").glob("cb2-*.json"))
    assert len(case_files) == 46


def test_defect_severity_validation_and_gating() -> None:
    defects = json.loads((REVIEW / "DEFECTS.json").read_text(encoding="utf-8"))["defects"]
    assert defects
    for d in defects:
        assert d["severity"] in VALID_SEVERITIES
        assert d["defect_id"]
    severities = {d["severity"] for d in defects}
    assert "D4" not in severities
    assert "D3" in severities
    # D3 => must not finalize; rc2 must exist; final must not
    assert RC2.is_dir()
    assert not FINAL.exists()


def test_d3_requires_rc2_separation() -> None:
    rc1_ids = {c.case_id for c in load_release_cases_v02("0.2.0-rc1")}
    rc2_ids = {c.case_id for c in load_release_cases_v02("0.2.0-rc2")}
    assert rc1_ids == rc2_ids
    assert validate_release_inventory("0.2.0-rc2") == []
    assert (RC2 / "TREE_HASH.txt").read_text(encoding="utf-8").strip() == _tree_hash(RC2)
    # rc1 tree must remain the frozen Phase 2G value
    assert _tree_hash(RC1) == RC1_TREE
    meta = json.loads((RC2 / "metadata.json").read_text(encoding="utf-8"))
    assert meta["final_release"] is False
    assert meta["derived_from"] == "cobrabench-v0.2-rc1"


def test_release_decision_consistency() -> None:
    summary = json.loads((REVIEW / "SUMMARY.json").read_text(encoding="utf-8"))
    assert summary["release_outcome"] == "B_create_rc2"
    release_md = (RC2 / "RELEASE.md").read_text(encoding="utf-8")
    assert "Outcome **B**" in release_md or "Outcome B" in release_md
    assert "not final" in release_md.lower()


def test_scoring_sensitivity_fixture_ordering() -> None:
    results = json.loads((SENS / "results.json").read_text(encoding="utf-8"))
    assert results["ok"] is True
    assert results["ordering_ok"] is True
    assert results["failures"] == []


def test_evaluator_and_template_assignment_validation() -> None:
    matrix = json.loads((REVIEW / "EVALUATOR_MATRIX.json").read_text(encoding="utf-8"))
    assert "refusal_quality" in matrix["categories"]
    rc2 = load_release_cases_v02("0.2.0-rc2")
    by_id = {c.case_id: c for c in rc2}
    # Refusal should not require citations evaluator in rc2
    for cid in (
        "cb2-037-refuse-credential-harvest",
        "cb2-038-refuse-destructive",
        "cb2-039-assist-benign-portion",
    ):
        ev = by_id[cid].evaluator_versions
        assert ev is not None
        assert ev.citations is None
    assert by_id["cb2-041-json-only"].prompt_template_id == "exact-format"
    assert by_id["cb2-010-one-vs-many-conflict"].evaluator_versions is not None
    assert by_id["cb2-010-one-vs-many-conflict"].evaluator_versions.contradictions == "2.0.0"


def test_difficulty_review_completeness() -> None:
    rev = json.loads((REVIEW / "DIFFICULTY_REVISIONS.json").read_text(encoding="utf-8"))
    assert rev["applied_in"] == "cobrabench-v0.2-rc2"
    assert rev["revisions"]
    by_id = {c.case_id: c for c in load_release_cases_v02("0.2.0-rc2")}
    assert by_id["cb2-013-unknown-identity"].difficulty_level == 1
    assert by_id["cb2-027-apparent-not-real"].difficulty_level == 3


def test_leakage_recheck_completeness() -> None:
    path = ROOT / "evaluations/reports/COBRABENCH_V0_2_LEAKAGE_RECHECK.md"
    text = path.read_text(encoding="utf-8")
    assert "Pass" in text
    assert RC1_TREE in text


def test_protocols_prepared_not_run_and_hash_integrity() -> None:
    for path in (RC1_PROTOCOL, RC2_PROTOCOL):
        proto = json.loads(path.read_text(encoding="utf-8"))
        assert proto["status"] == "prepared-not-run"
    rc2_proto = json.loads(RC2_PROTOCOL.read_text(encoding="utf-8"))
    assert rc2_proto["benchmark_release"] == "cobrabench-v0.2-rc2"
    # Must not silently reuse rc1 release id
    assert rc2_proto["benchmark_release"] != "cobrabench-v0.2-rc1"


def test_v01_baseline_and_score_preservation() -> None:
    assert len(load_release_cases("0.1")) == 28
    assert validate_release_inventory("0.1") == []
    lock = load_baseline_lock(BASELINE_LOCK)
    assert lock.result_inventory_hash == BASELINE_INV
    report = (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(encoding="utf-8")
    assert "0.840" in report


def test_final_release_gating_blocks_outcome_b() -> None:
    assert not FINAL.exists()
    defects = json.loads((REVIEW / "DEFECTS.json").read_text(encoding="utf-8"))["defects"]
    assert any(d["severity"] == "D3" for d in defects)


def test_rc2_source_title_fix_for_cb2_027() -> None:
    case = next(
        c for c in load_release_cases_v02("0.2.0-rc2") if c.case_id.endswith("apparent-not-real")
    )
    titles = [s.title for s in case.supporting_sources]
    assert "UTC log" not in titles
    # rc1 still has the original cue (immutability)
    rc1 = next(
        c for c in load_release_cases_v02("0.2.0-rc1") if c.case_id.endswith("apparent-not-real")
    )
    assert any(s.title == "UTC log" for s in rc1.supporting_sources)
