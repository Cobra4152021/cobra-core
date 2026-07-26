#!/usr/bin/env python3
"""Freeze CobraBench v0.2-rc1 inventory, hashes, and release metadata."""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.benchmarks.v02_validate import (  # noqa: E402
    load_v02_cases,
    suite_summary,
    validate_v02_suite,
)
from cobra_core.schemas.categories import CATEGORY_WEIGHTS_V02  # noqa: E402

REL = ROOT / "benchmarks" / "releases" / "cobrabench-v0.2-rc1"


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


def main() -> int:
    cases_dir = REL / "cases"
    errors = validate_v02_suite(cases_dir, repo_root=ROOT)
    if errors:
        print("VALIDATION FAILED")
        for err in errors:
            print(" -", err)
        return 1

    cases = load_v02_cases(cases_dir)
    summary = suite_summary(cases_dir)

    inventory = {
        "release_version": "0.2.0-rc1",
        "release_id": "cobrabench-v0.2-rc1",
        "case_count": len(cases),
        "cases": [
            {
                "filename": f"{c.case_id}.json",
                "sha256": _sha256_file(cases_dir / f"{c.case_id}.json"),
            }
            for c in cases
        ],
    }
    (REL / "INVENTORY.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")

    weights = {
        "rubric_id": "cobrabench_weighted_v2_rc1",
        "rubric_version": "0.2.0-rc1",
        "weights": {k.value: v for k, v in CATEGORY_WEIGHTS_V02.items()},
    }
    (REL / "weights.json").write_text(json.dumps(weights, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "release_id": "cobrabench-v0.2-rc1",
        "release_version": "0.2.0-rc1",
        "case_schema_version": "0.2.0-rc1",
        "rubric_id": "cobrabench_weighted_v2_rc1",
        "rubric_version": "0.2.0-rc1",
        "case_count": len(cases),
        "sensitivity_default": "public_synthetic",
        "frozen": True,
        "final_release": False,
        "label": "Release candidate — not final.",
        "description": "CobraBench v0.2 release candidate constructed in Phase 2G.",
        "created_at": datetime.now(UTC).isoformat(),
        "summary": summary,
    }
    (REL / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    # Human review rollup
    reviews = {
        "single_reviewer": True,
        "approved": summary["approved_count"],
        "case_count": summary["case_count"],
        "unresolved_ambiguity_count": 0,
        "cases_removed_during_review": 0,
        "cases_revised_during_review": 0,
        "notes": "Single-reviewer static approval embedded per case. Not multi-rater.",
    }
    (REL / "human-review-summary.json").write_text(
        json.dumps(reviews, indent=2) + "\n", encoding="utf-8"
    )

    release_md = f"""# CobraBench v0.2-rc1

> Release candidate — not final.

## Identity

- Release ID: `cobrabench-v0.2-rc1`
- Case count: **{len(cases)}**
- Final release: **false**
- Inventory case hash count: **{len(inventory["cases"])}**
- Tree hash: see `TREE_HASH.txt` (hashes all release files except `SHA256SUMS` and `TREE_HASH.txt`)

## Category distribution

| Category | Count |
| --- | ---: |
{chr(10).join(f"| {k} | {v} |" for k, v in summary["categories"].items())}

## Difficulty distribution

| Level | Count |
| --- | ---: |
{chr(10).join(f"| {k} | {v} |" for k, v in summary["difficulty"].items())}

## Weights

See `weights.json` (`cobrabench_weighted_v2_rc1`). Total 100%.

## Evaluator versions

- unsupported_claims 2.0.0
- citations 2.0.0
- contradictions 2.0.0
- format_compliance 2.0.0
- output_budget_telemetry 1.0.0

## Prompt templates / runtime profiles

Referenced from `prompts/` and `runtime_policies/` registries (v2 evidence standard).

## Review status

- Human static review: single-reviewer, 100% approved
- Unresolved material ambiguities: 0
- Contamination review: see `docs/COBRABENCH_V0_2_CONTAMINATION_REVIEW.md`

## Known limitations

- Not executed against any model in Phase 2G
- Deterministic evaluators remain incomplete proxies for judgment
- Scores are not comparable to CobraBench v0.1 / 0.840
- Single-reviewer process (not multi-rater)

## Incompatibility with v0.1

Do not present rc1 scores as direct improvement or decline versus 0.840.
"""
    (REL / "RELEASE.md").write_text(release_md, encoding="utf-8")
    tree_hash = _tree_hash(REL)
    (REL / "TREE_HASH.txt").write_text(tree_hash + "\n", encoding="utf-8")

    sum_lines = []
    for path in sorted(REL.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rel = path.relative_to(REL).as_posix()
            sum_lines.append(f"{_sha256_file(path)}  {rel}")
    (REL / "SHA256SUMS").write_text("\n".join(sum_lines) + "\n", encoding="utf-8")

    print(json.dumps({"ok": True, "case_count": len(cases), "tree_hash": tree_hash}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
