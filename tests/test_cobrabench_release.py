"""Frozen CobraBench v0.1 release inventory tests."""

from __future__ import annotations

import json
from pathlib import Path

from cobra_core.benchmarks.release import (
    assert_no_duplicate_case_ids,
    category_distribution,
    load_release_cases,
    validate_release_inventory,
)
from cobra_core.schemas.categories import weights_sum


def test_release_has_twenty_eight_cases() -> None:
    cases = load_release_cases("0.1")
    assert len(cases) == 28


def test_inventory_valid_and_case_count() -> None:
    errors = validate_release_inventory("0.1")
    assert errors == []
    inventory = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "benchmarks"
            / "releases"
            / "cobrabench-v0.1"
            / "INVENTORY.json"
        ).read_text(encoding="utf-8")
    )
    assert inventory["case_count"] == 28


def test_no_duplicate_case_ids() -> None:
    cases = load_release_cases("0.1")
    assert_no_duplicate_case_ids(cases)
    assert len({case.case_id for case in cases}) == len(cases)


def test_category_distribution_nonzero() -> None:
    cases = load_release_cases("0.1")
    counts = category_distribution(cases)
    assert sum(counts.values()) == 28
    assert all(count >= 0 for count in counts.values())


def test_weights_sum_to_one() -> None:
    assert abs(weights_sum() - 1.0) < 1e-9


def test_train_split_protection(repo_root: Path) -> None:
    release_case_ids = {case.case_id for case in load_release_cases("0.1")}
    curated = repo_root / "datasets" / "curated"
    if curated.exists():
        overlap: set[str] = set()
        for path in curated.rglob("*"):
            if not path.is_file() or path.name in {".gitkeep", "README.md"}:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for case_id in release_case_ids:
                if case_id in text:
                    overlap.add(case_id)
        assert not overlap, f"curated data overlaps release case_ids: {overlap}"
