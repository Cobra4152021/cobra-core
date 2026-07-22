#!/usr/bin/env python3
"""Build Phase 2E static case-level weakness analysis artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.analysis.baseline_lock import (  # noqa: E402
    assert_path_outside_locked_baseline,
)
from cobra_core.analysis.case_analysis import build_case_analyses  # noqa: E402

DEFAULT_RUN = (
    ROOT / "evaluations" / "results" / "cobrabench-v0.1" / "qwen3-8b" / "20260722T200000Z-8bba5e01"
)
DEFAULT_OUTPUT = ROOT / "evaluations" / "analysis" / "qwen3-8b-v0.1-case-analysis.json"
DEFAULT_REPORT = ROOT / "evaluations" / "reports" / "QWEN3_8B_CASE_LEVEL_ANALYSIS.md"
DEFAULT_LOCK = ROOT / "evaluations" / "baselines" / "qwen3-8b-cobrabench-v0.1.json"


def _group_cases(analyses: list) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for item in analyses:
        score = item.baseline_score
        primary = item.primary_weakness_class
        priority = item.diagnostic_priority.value
        rerun = item.rerun_justified

        if score >= 0.9 and primary is None:
            groups["clearly strong"].append(item.case_id)
        elif score >= 0.75 and primary is None:
            groups["acceptable but improvable"].append(item.case_id)
        elif item.confidence.value == "low" or (primary is None and 0.55 <= score < 0.75):
            groups["ambiguous"].append(item.case_id)
        elif primary and primary.value == "M":
            groups["likely model weakness"].append(item.case_id)
        elif primary and primary.value in {"S", "B"}:
            groups["likely benchmark/scoring weakness"].append(item.case_id)
        elif primary and primary.value == "L":
            groups["likely output-cap limitation"].append(item.case_id)
        else:
            groups["acceptable but improvable"].append(item.case_id)

        if rerun or priority in {"medium", "high"}:
            groups["requires controlled rerun"].append(item.case_id)

    return groups


def write_report(analyses: list, report_path: Path, run_id: str) -> None:
    groups = _group_cases(analyses)
    primary_counts = Counter(
        item.primary_weakness_class.value if item.primary_weakness_class else "none"
        for item in analyses
    )

    lines = [
        "# Qwen3-8B Case-Level Weakness Analysis",
        "",
        f"**Run ID:** `{run_id}`  ",
        f"**Generated:** {datetime.now(UTC).isoformat()}  ",
        "**Scope:** Static analysis only — no new inference.",
        "",
        "## Summary",
        "",
        f"- Cases analyzed: **{len(analyses)}**",
        f"- Primary weakness class counts: {dict(primary_counts)}",
        f"- Rerun justified: **{sum(1 for a in analyses if a.rerun_justified)}** cases",
        "",
        "## Groupings",
        "",
    ]

    for group_name in [
        "clearly strong",
        "acceptable but improvable",
        "ambiguous",
        "likely model weakness",
        "likely benchmark/scoring weakness",
        "likely output-cap limitation",
        "requires controlled rerun",
    ]:
        case_ids = sorted(set(groups.get(group_name, [])))
        lines.append(f"### {group_name.title()}")
        lines.append("")
        if case_ids:
            for cid in case_ids:
                match = next(a for a in analyses if a.case_id == cid)
                primary = (
                    match.primary_weakness_class.value if match.primary_weakness_class else "none"
                )
                lines.append(
                    f"- `{cid}` — score {match.baseline_score:.2f}, "
                    f"primary={primary}, observed: {match.observed_weakness}"
                )
        else:
            lines.append("_None_")
        lines.append("")

    lines.extend(
        [
            "## Per-case table",
            "",
            "| Case | Category | Score | Primary | Contributing | Rerun |",
            "|------|----------|-------|---------|--------------|-------|",
        ]
    )
    for item in analyses:
        primary = item.primary_weakness_class.value if item.primary_weakness_class else "—"
        contrib = ",".join(c.value for c in item.contributing_classes) or "—"
        rerun = "yes" if item.rerun_justified else "no"
        lines.append(
            f"| `{item.case_id}` | {item.category} | {item.baseline_score:.2f} | "
            f"{primary} | {contrib} | {rerun} |"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    run = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
    analyses = build_case_analyses(args.run_dir)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run_id": run["run_id"],
        "model_slug": run["model_slug"],
        "benchmark_version": run["benchmark_version"],
        "analysis_version": "phase-2e-static-v1",
        "case_count": len(analyses),
        "cases": [item.model_dump(mode="json") for item in analyses],
    }

    assert_path_outside_locked_baseline(DEFAULT_LOCK, args.output, repo_root=ROOT)
    assert_path_outside_locked_baseline(DEFAULT_LOCK, args.report, repo_root=ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_report(analyses, args.report, run["run_id"])

    print(f"Wrote {args.output}")
    print(f"Wrote {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
