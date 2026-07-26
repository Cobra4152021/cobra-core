"""Phase 3A: reviewer kit + Milestone M1 governance (no model; no benchmark edits)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cobra_core.analysis.baseline_lock import load_baseline_lock
from cobra_core.benchmarks.release import validate_release_inventory

ROOT = Path(__file__).resolve().parents[1]

BASELINE_INV = "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
RC1_INV = "87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87"
RC1_TREE = "3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10"
RC2_INV = "08f04c10267b3f772d7783a332d816947486812f7a983dff070bdad442708cc6"
RC2_TREE = "1d438415c22827155f57817ace9274aee6c9e47048e4f6443a249ba7a5f2314f"

REVIEWER_KIT_FILES = [
    "README.md",
    "OVERVIEW.md",
    "REVIEW_PROCESS.md",
    "REVIEW_CHECKLIST.md",
    "DEFECT_GUIDE.md",
    "QUESTION_TEMPLATE.md",
    "CASE_REVIEW_FORM.md",
    "SUMMARY_REPORT_TEMPLATE.md",
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tree_hash(root: Path) -> str:
    entries: list[str] = []
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()
    ):
        if path.is_file() and path.name not in {"TREE_HASH.txt", "SHA256SUMS"}:
            rel = path.relative_to(root).as_posix()
            entries.append(f"{rel}:{_sha(path)}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def _inv_hash(root: Path) -> str:
    inv = json.loads((root / "INVENTORY.json").read_text(encoding="utf-8"))
    payload = "\n".join(f"{e['filename']}:{e['sha256']}" for e in inv["cases"])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def test_reviewer_kit_files_exist() -> None:
    kit = ROOT / "reviewer-kit"
    assert kit.is_dir()
    for name in REVIEWER_KIT_FILES:
        path = kit / name
        assert path.is_file(), name
        assert path.stat().st_size > 50


def test_milestone_roadmap_policy_adr_exist() -> None:
    assert (ROOT / "docs/milestones/M1_Benchmark_Freeze.md").is_file()
    assert (ROOT / "docs/ROADMAP.md").is_file()
    assert (ROOT / "docs/EVALUATION_POLICY.md").is_file()
    assert (ROOT / "docs/decisions/ADR-0009-review-governance.md").is_file()
    m1 = (ROOT / "docs/milestones/M1_Benchmark_Freeze.md").read_text(encoding="utf-8")
    assert "0.840" in m1
    assert RC2_TREE in m1
    assert "neither rc1 nor rc2 supersede" in m1.lower() or "Neither rc1 nor rc2 supersede" in m1


def test_frozen_hashes_unchanged() -> None:
    lock = load_baseline_lock(ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json")
    assert lock.result_inventory_hash == BASELINE_INV
    rc1 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc1"
    rc2 = ROOT / "benchmarks/releases/cobrabench-v0.2-rc2"
    assert _inv_hash(rc1) == RC1_INV
    assert _tree_hash(rc1) == RC1_TREE
    assert _inv_hash(rc2) == RC2_INV
    assert _tree_hash(rc2) == RC2_TREE
    assert validate_release_inventory("0.1") == []
    assert validate_release_inventory("0.2.0-rc1") == []
    assert validate_release_inventory("0.2.0-rc2") == []


def test_evaluator_prompt_runtime_trees_stable_pins() -> None:
    """Phase 3A must not alter evaluator/prompt/runtime version directories."""
    expected = {
        "evaluators/unsupported_claims/v2/metadata.json": (
            "3585e31b9ee35db45117edf19074b6d86f8114d3f2702c7f95cbe85206b7fe03"
        ),
        "evaluators/citations/v2/metadata.json": (
            "4355672113afafa745a88bed77e80525be87127b7ee9ce778fffb7dfdf96077d"
        ),
        "prompts/evidence-analysis/v2.yaml": (
            "589ff91f80126fda0d36629c26562f9b0c4891a1b99c335e9b78edd858351b3c"
        ),
        "prompts/registry.json": (
            "c7ef15dab37786631d21eccb8c4f61aca7e45d4467f1299d0529965fdfdea823"
        ),
        "runtime_policies/deterministic-investigation.yaml": (
            "275c9b85607da688e5aed0e9e4f31a4bc27559b2218c4632cc9a79f62af5f653"
        ),
    }
    for rel, digest in expected.items():
        path = ROOT / rel
        assert path.is_file(), rel
        assert _sha(path) == digest, rel


def test_blind_review_required_in_kit() -> None:
    process = (ROOT / "reviewer-kit/REVIEW_PROCESS.md").read_text(encoding="utf-8")
    assert "Blind" in process or "blind" in process
    assert "expected_behaviors" in process
    form = (ROOT / "reviewer-kit/CASE_REVIEW_FORM.md").read_text(encoding="utf-8")
    assert "Blind" in form
