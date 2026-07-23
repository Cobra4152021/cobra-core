"""Phase 2I second-review gating tests (no model load)."""

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
REVIEW = ROOT / "evaluations/reviews/cobrabench-v0.2-rc2-second-independent-review"
RC1 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc1"
RC2 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
FINAL = ROOT / "benchmarks/releases/cobrabench-v0.2"
RC3 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc3"
BASELINE_LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
UC_METRICS = ROOT / "evaluations/fixtures/unsupported-claims-v2-false-negative/metrics.json"
CONTRA = ROOT / "evaluations/fixtures/contradiction-v2-sensitivity/results.json"
RC2_PROTOCOL = ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json"

RC1_TREE = "3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10"
RC1_INV = "87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87"
RC2_TREE = "1d438415c22827155f57817ace9274aee6c9e47048e4f6443a249ba7a5f2314f"
RC2_INV = "08f04c10267b3f772d7783a332d816947486812f7a983dff070bdad442708cc6"
BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path) -> str:
    entries: list[str] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name not in {"TREE_HASH.txt", "SHA256SUMS"}:
            rel = path.relative_to(root).as_posix()
            entries.append(f"{rel}:{_sha(path)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def _inv_hash(root: Path) -> str:
    inv = json.loads((root / "INVENTORY.json").read_text(encoding="utf-8"))
    payload = "\n".join(f"{e['filename']}:{e['sha256']}" for e in inv["cases"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_blind_review_record_completeness() -> None:
    blind = json.loads((REVIEW / "BLIND_ANSWERABILITY.json").read_text(encoding="utf-8"))
    assert len(blind["cases"]) == 46
    assert all(c["rubric_consulted"] is False for c in blind["cases"])
    assert all(c["blind_pass"] is True for c in blind["cases"])
    assert len(list((REVIEW / "blind").glob("cb2-*.json"))) == 46


def test_rubric_comparison_completeness() -> None:
    rubric = json.loads((REVIEW / "RUBRIC_COMPARISON.json").read_text(encoding="utf-8"))
    assert len(rubric["cases"]) == 46
    assert all(c["rubric_consulted"] is True for c in rubric["cases"])


def test_all_seventeen_revision_verifications() -> None:
    rev = json.loads((REVIEW / "REVISION_VERIFICATION.json").read_text(encoding="utf-8"))
    assert len(rev["revisions"]) == 17
    assert all(r["correction_verified"] for r in rev["revisions"])
    assert sum(1 for r in rev["revisions"] if r["new_defect_introduced"]) == 0


def test_unsupported_claim_false_negative_fixtures() -> None:
    metrics = json.loads(UC_METRICS.read_text(encoding="utf-8"))
    assert metrics["adversarial_n"] == 10
    assert 0.0 <= metrics["true_positive_rate"] <= 1.0
    assert 0.0 <= metrics["false_negative_rate"] <= 1.0
    assert 0.0 <= metrics["cannot_determine_rate_on_adversarial"] <= 1.0
    # Known Phase 2I measurement: FN risk is material on this fixture set
    assert metrics["false_negative_rate"] >= 0.5


def test_contradiction_sensitivity_ordering() -> None:
    data = json.loads(CONTRA.read_text(encoding="utf-8"))
    assert data["ordering_ok"] is True
    assert len(data["results"]) >= 8


def test_small_sample_documentation() -> None:
    refusal = (ROOT / "evaluations/reports/COBRABENCH_V0_2_SMALL_SAMPLE_REVIEW.md").read_text(
        encoding="utf-8"
    )
    assert "Refusal" in refusal
    assert "Uncertainty" in refusal
    assert "small-sample" in refusal.lower() or "n=3" in refusal or "Three cases" in refusal


def test_diversity_review_completeness() -> None:
    path = ROOT / "evaluations/reports/COBRABENCH_V0_2_RC2_DIVERSITY_REVIEW.md"
    text = path.read_text(encoding="utf-8")
    assert "Diversity" in text or "diversity" in text
    assert (REVIEW / "DIVERSITY.json").is_file()


def test_defect_register_validation() -> None:
    defects = json.loads((REVIEW / "defects.json").read_text(encoding="utf-8"))["defects"]
    assert defects
    for d in defects:
        assert d["severity"] in {"D0", "D1", "D2", "D3", "D4"}
        assert d["status"] in {
            "accepted",
            "fixed in proposed rc3",
            "documentation-only",
            "rejected with rationale",
            "unresolved",
        }
    assert any(d["defect_id"] == "D2I-IND-001" and d["severity"] == "D4" for d in defects)


def test_d3_d4_final_release_blocking_and_independence() -> None:
    summary = json.loads((REVIEW / "SUMMARY.json").read_text(encoding="utf-8"))
    independence = json.loads((REVIEW / "INDEPENDENCE.json").read_text(encoding="utf-8"))
    assert independence["genuine_separation_achieved"] is False
    assert summary["release_outcome"] == "D_keep_rc2_non_final"
    assert summary["final_v02_created"] is False
    assert summary["rc3_created"] is False
    assert not FINAL.exists()
    assert not RC3.exists()


def test_rc2_immutability_and_rc3_separation() -> None:
    assert validate_release_inventory("0.2.0-rc2") == []
    assert _tree_hash(RC2) == RC2_TREE
    assert _inv_hash(RC2) == RC2_INV
    assert (RC2 / "TREE_HASH.txt").read_text(encoding="utf-8").strip() == RC2_TREE
    # rc1 still frozen
    assert _tree_hash(RC1) == RC1_TREE
    assert _inv_hash(RC1) == RC1_INV


def test_protocol_prepared_not_run() -> None:
    proto = json.loads(RC2_PROTOCOL.read_text(encoding="utf-8"))
    assert proto["status"] == "prepared-not-run"
    assert not (ROOT / "evaluations/protocols/qwen3-8b-cobrabench-v0.2.json").exists()


def test_v01_baseline_and_0840_preservation() -> None:
    assert len(load_release_cases("0.1")) == 28
    assert validate_release_inventory("0.1") == []
    lock = load_baseline_lock(BASELINE_LOCK)
    assert lock.result_inventory_hash == BASELINE_INV
    report = (ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md").read_text(encoding="utf-8")
    assert "0.840" in report
    # rc2 still 46 cases
    assert len(load_release_cases_v02("0.2.0-rc2")) == 46
