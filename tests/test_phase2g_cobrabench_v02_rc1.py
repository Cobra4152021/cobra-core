"""Phase 2G CobraBench v0.2-rc1 tests (no model load)."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest

from cobra_core.analysis.baseline_lock import load_baseline_lock, validate_baseline_lock
from cobra_core.benchmarks.release import (
    load_release_cases,
    load_release_cases_v02,
    validate_release_inventory,
)
from cobra_core.benchmarks.v02_validate import validate_v02_suite
from cobra_core.evaluation.citations import extract_citation_keys
from cobra_core.evaluators.citations.v2 import evaluate_citations_v2
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2
from cobra_core.evaluators.format_compliance.parser import ParserMode, parse_finding_risk_next
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2
from cobra_core.evaluators.unsupported_claims.v2 import evaluate_unsupported_claims_v2
from cobra_core.schemas.categories import (
    CATEGORY_WEIGHTS,
    CATEGORY_WEIGHTS_V02,
    BenchmarkCategory,
    weights_sum_v02,
)

ROOT = Path(__file__).resolve().parents[1]
RC_DIR = ROOT / "benchmarks" / "releases" / "cobrabench-v0.2-rc1"
DRAFT_DIR = ROOT / "benchmarks" / "drafts" / "cobrabench-v0.2"
V01_DIR = ROOT / "benchmarks" / "releases" / "cobrabench-v0.1"
PROTOCOL = ROOT / "evaluations" / "protocols" / "qwen3-8b-cobrabench-v0.2-rc1.json"
FIXTURES = ROOT / "evaluations" / "fixtures" / "cobrabench-v0.2-rc1-scoring" / "fixtures.json"
FIXTURE_RESULTS = ROOT / "evaluations" / "fixtures" / "cobrabench-v0.2-rc1-scoring" / "results.json"
BASELINE_LOCK = ROOT / "evaluations" / "baselines" / "qwen3-8b-cobrabench-v0.1.json"

EXPECTED_CATEGORY_COUNTS = {
    "investigation_reasoning": 6,
    "evidence_grounding": 6,
    "hallucination_resistance": 5,
    "citation_correctness": 5,
    "contradiction_detection": 6,
    "coding": 4,
    "long_document_analysis": 4,
    "refusal_quality": 3,
    "instruction_following": 4,
    "uncertainty_calibration": 3,
}


def _tree_hash(root: Path) -> str:
    entries: list[str] = []
    for path in sorted(
        root.rglob("*"), key=lambda item: item.relative_to(root).as_posix().casefold()
    ):
        if path.is_file() and path.name not in {"TREE_HASH.txt", "SHA256SUMS"}:
            rel = path.relative_to(root).as_posix()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(f"{rel}:{digest}")
    return hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()


def test_v02_rc1_case_count_and_schema() -> None:
    cases = load_release_cases_v02("0.2.0-rc1")
    assert 40 <= len(cases) <= 48
    assert len(cases) == 46
    for case in cases:
        assert case.status == "release_candidate"
        assert case.official_release is False
        assert case.part_of_cobrabench_v01 is False
        assert case.frozen is True
        assert case.case_id.startswith("cb2-")
        assert case.human_review is not None
        assert case.human_review.approval_status == "approved"
        assert not case.human_review.unresolved_ambiguity
        assert case.contamination is not None
        assert case.contamination.synthetic is True


def test_unique_source_keys_and_evidence_refs() -> None:
    cases = load_release_cases_v02()
    for case in cases:
        keys = [s.citation_key for s in case.supporting_sources]
        assert len(keys) == len(set(keys))
        if case.material_evidence:
            for key in (
                case.material_evidence.required_evidence_ids
                + case.material_evidence.optional_evidence_ids
                + case.material_evidence.contrary_evidence_ids
            ):
                if keys:
                    assert key in keys, f"{case.case_id}: missing {key}"


def test_evaluator_prompt_runtime_integrity() -> None:
    errors = validate_v02_suite(RC_DIR / "cases", repo_root=ROOT)
    assert errors == []


def test_category_weight_totals_and_distribution() -> None:
    assert abs(weights_sum_v02() - 1.0) < 1e-9
    assert abs(sum(CATEGORY_WEIGHTS.values()) - 1.0) < 1e-9
    assert BenchmarkCategory.UNCERTAINTY_CALIBRATION in CATEGORY_WEIGHTS_V02
    assert BenchmarkCategory.UNCERTAINTY_CALIBRATION not in CATEGORY_WEIGHTS
    cases = load_release_cases_v02()
    dist = {k.value: v for k, v in Counter(c.category for c in cases).items()}
    assert dist == EXPECTED_CATEGORY_COUNTS


def test_difficulty_distribution() -> None:
    cases = load_release_cases_v02()
    levels = Counter(c.difficulty_level for c in cases)
    assert set(levels) <= {1, 2, 3, 4}
    assert sum(levels.values()) == 46


def test_draft_versus_release_candidate_separation() -> None:
    draft_ids = {p.stem for p in DRAFT_DIR.glob("*.json")} if DRAFT_DIR.exists() else set()
    rc_ids = {c.case_id for c in load_release_cases_v02()}
    assert not (draft_ids & rc_ids)
    release_md = (RC_DIR / "RELEASE.md").read_text(encoding="utf-8")
    assert "not final" in release_md.lower()
    assert "Release candidate" in release_md


def test_contamination_and_near_duplicate_metadata() -> None:
    cases = load_release_cases_v02()
    titles = [c.title.lower().strip() for c in cases]
    assert len(titles) == len(set(titles))
    for case in cases:
        assert case.contamination is not None
        assert case.contamination.training_set_exclusion_status
        assert case.contamination.pretraining_exposure_risk == "low"
        assert case.contamination.answer_leakage_risk == "low"


def test_human_review_completeness_blocks_unresolved() -> None:
    cases = load_release_cases_v02()
    assert all(c.human_review and c.human_review.single_reviewer for c in cases)
    summary = json.loads((RC_DIR / "human-review-summary.json").read_text(encoding="utf-8"))
    assert summary["approved"] == 46
    assert summary["unresolved_ambiguity_count"] == 0


def test_release_inventory_and_tree_hash() -> None:
    assert validate_release_inventory("0.2.0-rc1") == []
    recorded = (RC_DIR / "TREE_HASH.txt").read_text(encoding="utf-8").strip()
    assert recorded == _tree_hash(RC_DIR)
    inventory = json.loads((RC_DIR / "INVENTORY.json").read_text(encoding="utf-8"))
    assert inventory["case_count"] == 46
    assert len(inventory["cases"]) == 46


def test_protocol_prepared_not_run() -> None:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["status"] == "prepared-not-run"
    assert protocol["benchmark_release"] == "cobrabench-v0.2-rc1"
    assert protocol["model_revision"] == "b968826d9c46dd6066d109eabc6255188de91218"


def test_v01_immutability_and_baseline_lock() -> None:
    v01_cases = load_release_cases("0.1")
    assert len(v01_cases) == 28
    assert validate_release_inventory("0.1") == []
    lock = load_baseline_lock(BASELINE_LOCK)
    assert (
        lock.result_inventory_hash
        == "84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6"
    )
    # Full lock validation may require local result trees; hash field is the Phase 2D gate.
    _ = validate_baseline_lock
    meta = json.loads((V01_DIR / "INVENTORY.json").read_text(encoding="utf-8"))
    assert meta["case_count"] == 28


def test_scoring_fixture_direction() -> None:
    assert FIXTURES.is_file()
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert len(data["fixtures"]) >= 8

    fmt = evaluate_format_compliance_v2(
        "FINDING: Scanner found one outdated dependency.\n"
        "RISK: Security exposure from outdated package.\n"
        "NEXT: Update the dependency.\n"
    )
    assert fmt.semantic_score >= 0.9
    assert fmt.parse_success is True

    markdown = "- **FINDING:** a\n- **RISK:** b\n- **NEXT:** c\n"
    strict = parse_finding_risk_next(markdown, mode=ParserMode.STRICT)
    tolerant = parse_finding_risk_next(markdown, mode=ParserMode.TOLERANT)
    assert strict.success is False
    assert tolerant.success is True

    assert extract_citation_keys("Claim [S1] and [S2].") == ["S1", "S2"]
    cit = evaluate_citations_v2(
        "A [S1]. B [S2].",
        allowed_keys=["S1", "S2"],
        required_evidence_ids=["S1", "S2"],
    )
    assert cit.citation_precision == 1.0
    assert cit.evidence_coverage == 1.0

    strong = evaluate_contradictions_v2(
        "S1 and S2 contradict: 120 versus 95. Preserve both. Request recount. Uncertain."
    )
    weak = evaluate_contradictions_v2("Everything looks fine.")
    assert strong.detection > weak.detection

    uc = evaluate_unsupported_claims_v2(
        "Scanner found one outdated dependency in demo app [S1].",
        ["S1"],
        {"S1": "Scanner found one outdated dependency in demo app."},
    )
    assert uc.unsupported_flag_count == 0

    if FIXTURE_RESULTS.is_file():
        results = json.loads(FIXTURE_RESULTS.read_text(encoding="utf-8"))
        assert results.get("ok") is True


def test_load_release_cases_rejects_v02_on_v01_loader() -> None:
    with pytest.raises(ValueError, match="load_release_cases_v02"):
        load_release_cases("0.2.0-rc1")


def test_weights_json_matches_category_weights_v02() -> None:
    weights = json.loads((RC_DIR / "weights.json").read_text(encoding="utf-8"))
    assert weights["weights"] == {k.value: v for k, v in CATEGORY_WEIGHTS_V02.items()}


def test_draft_cases_remain_non_official() -> None:
    if not DRAFT_DIR.exists():
        return
    for path in DRAFT_DIR.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data.get("official_release") is False
        assert data.get("status") in {"draft", "non_official"}
        assert data["case_id"].startswith("draft-")
