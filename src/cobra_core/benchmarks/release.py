"""Load and validate frozen CobraBench release bundles."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any

from cobra_core.schemas.benchmark import BenchmarkCase
from cobra_core.schemas.benchmark_v02 import BenchmarkCaseV02
from cobra_core.schemas.categories import BenchmarkCategory

_RELEASE_VERSION_DIRS: dict[str, str] = {
    "0.1": "cobrabench-v0.1",
    "0.2.0-rc1": "cobrabench-v0.2-rc1",
    "0.2-rc1": "cobrabench-v0.2-rc1",
    "0.2.0-rc2": "cobrabench-v0.2-rc2",
    "0.2-rc2": "cobrabench-v0.2-rc2",
}

_V02_RELEASE_VERSIONS = frozenset({"0.2.0-rc1", "0.2-rc1", "0.2.0-rc2", "0.2-rc2"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def release_dir(version: str = "0.1") -> Path:
    """Return the path to a frozen release directory."""
    slug = _RELEASE_VERSION_DIRS.get(version)
    if slug is None:
        msg = f"Unknown CobraBench release version: {version!r}"
        raise ValueError(msg)
    return _repo_root() / "benchmarks" / "releases" / slug


RELEASE_DIR = release_dir("0.1")


def load_release_cases(version: str = "0.1") -> list[BenchmarkCase]:
    """Load and validate all case files from a frozen v0.1 release."""
    if version in _V02_RELEASE_VERSIONS:
        msg = f"Use load_release_cases_v02({version!r}) for CobraBench v0.2 release candidates"
        raise ValueError(msg)
    cases_dir = release_dir(version) / "cases"
    cases: list[BenchmarkCase] = []
    for path in sorted(cases_dir.glob("*.json")):
        cases.append(BenchmarkCase.model_validate_json(path.read_text(encoding="utf-8")))
    assert_no_duplicate_case_ids(cases)
    return cases


def load_release_cases_v02(version: str = "0.2.0-rc1") -> list[BenchmarkCaseV02]:
    """Load and validate all case files from a frozen v0.2 release candidate."""
    if version not in _V02_RELEASE_VERSIONS:
        msg = f"Unknown CobraBench v0.2 release version: {version!r}"
        raise ValueError(msg)
    cases_dir = release_dir(version) / "cases"
    cases: list[BenchmarkCaseV02] = []
    for path in sorted(cases_dir.glob("*.json")):
        cases.append(BenchmarkCaseV02.model_validate_json(path.read_text(encoding="utf-8")))
    assert_no_duplicate_case_ids(cases)
    return cases


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def validate_release_inventory(version: str = "0.1") -> list[str]:
    """
    Verify INVENTORY.json matches case files and content hashes.

    Returns a list of error messages; empty list means the inventory is valid.
    """
    root = release_dir(version)
    inventory_path = root / "INVENTORY.json"
    cases_dir = root / "cases"
    errors: list[str] = []

    if not inventory_path.is_file():
        return [f"Missing inventory file: {inventory_path}"]

    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    entries: list[dict[str, Any]] = inventory.get("cases", [])
    inventory_files = {entry["filename"]: entry for entry in entries}

    disk_files = sorted(path.name for path in cases_dir.glob("*.json"))
    inventory_names = sorted(inventory_files)

    if disk_files != inventory_names:
        errors.append(
            "Case file list mismatch between disk and INVENTORY.json: "
            f"disk={disk_files}, inventory={inventory_names}"
        )

    for filename in disk_files:
        path = cases_dir / filename
        expected_entry = inventory_files.get(filename)
        if expected_entry is None:
            continue
        actual_hash = _sha256_file(path)
        expected_hash = expected_entry.get("sha256")
        if actual_hash != expected_hash:
            errors.append(
                f"Hash mismatch for {filename}: expected {expected_hash}, got {actual_hash}"
            )

    return errors


def category_distribution(
    cases: list[BenchmarkCase] | list[BenchmarkCaseV02],
) -> dict[str, int]:
    """Count cases by primary category."""
    counts = Counter(case.category.value for case in cases)
    return {category.value: counts.get(category.value, 0) for category in BenchmarkCategory}


def assert_no_duplicate_case_ids(
    cases: list[BenchmarkCase] | list[BenchmarkCaseV02],
) -> None:
    """Raise ValueError if any case_id appears more than once."""
    seen: set[str] = set()
    duplicates: set[str] = set()
    for case in cases:
        if case.case_id in seen:
            duplicates.add(case.case_id)
        seen.add(case.case_id)
    if duplicates:
        dup_list = ", ".join(sorted(duplicates))
        msg = f"Duplicate benchmark case_id values: {dup_list}"
        raise ValueError(msg)
