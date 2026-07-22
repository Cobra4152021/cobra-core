#!/usr/bin/env python3
"""Generate sanitized baseline comparison reports from two CobraBench runs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.comparison import (  # noqa: E402
    compare_category_scores,
    compare_weighted_totals,
)

EXCERPT_LIMIT = 200


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _truncate(text: str, limit: int = EXCERPT_LIMIT) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3] + "..."


def _category_scores_from_run(run_dir: Path) -> dict[str, float]:
    rule_doc = _read_json(run_dir / "rule-checks.json")
    cases = rule_doc.get("cases", {})
    if not cases:
        return {}
    scores: list[float] = []
    for payload in cases.values():
        obj = payload.get("objective_score")
        beh = payload.get("behavior_score")
        if obj is not None and beh is not None:
            scores.append((float(obj) + float(beh)) / 2.0)
        elif obj is not None:
            scores.append(float(obj))
        elif beh is not None:
            scores.append(float(beh))
    if not scores:
        return {}
    avg = sum(scores) / len(scores)
    run_meta = _read_json(run_dir / "run.json")
    model_slug = run_meta.get("model_slug", "unknown")
    return {f"{model_slug}_objective_behavior_avg": round(avg, 4)}


def _case_rows(run_dir: Path) -> list[dict[str, Any]]:
    run_meta = _read_json(run_dir / "run.json")
    rule_doc = _read_json(run_dir / "rule-checks.json")
    rows: list[dict[str, Any]] = []
    for case in run_meta.get("cases", []):
        case_id = case.get("case_id")
        response_path = run_dir / "responses" / f"{case_id}.txt"
        excerpt = ""
        if response_path.is_file():
            excerpt = _truncate(response_path.read_text(encoding="utf-8"))
        case_rules = rule_doc.get("cases", {}).get(case_id, {})
        rows.append(
            {
                "case_id": case_id,
                "status": case.get("status"),
                "objective_score": case_rules.get("objective_score"),
                "behavior_score": case_rules.get("behavior_score"),
                "response_excerpt": excerpt,
            }
        )
    return rows


def _render_single_report(run_dir: Path, title: str) -> str:
    run_meta = _read_json(run_dir / "run.json")
    rows = _case_rows(run_dir)
    lines = [
        f"# {title}",
        "",
        "> Sanitized report — prompts omitted per contamination policy.",
        "",
        "## Run metadata",
        "",
        f"- run_id: `{run_meta.get('run_id')}`",
        f"- model_slug: `{run_meta.get('model_slug')}`",
        f"- benchmark_version: `{run_meta.get('benchmark_version')}`",
        f"- dry_run: `{run_meta.get('dry_run')}`",
        f"- case_count: `{run_meta.get('case_count', len(rows))}`",
        "",
        "## Case scores",
        "",
        "| case_id | status | objective | behavior | response_excerpt |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['case_id']} | {row['status']} | {row['objective_score']} | "
            f"{row['behavior_score']} | {row['response_excerpt']} |"
        )
    lines.append("")
    return "\n".join(lines)


def _render_comparison_report(run_a: Path, run_b: Path, title: str) -> str:
    meta_a = _read_json(run_a / "run.json")
    meta_b = _read_json(run_b / "run.json")
    scores_a = _category_scores_from_run(run_a)
    scores_b = _category_scores_from_run(run_b)
    comparison = compare_category_scores(scores_a, scores_b)
    totals = compare_weighted_totals(scores_a, scores_b)
    lines = [
        f"# {title}",
        "",
        "> Sanitized comparison — no full prompts; excerpts truncated to 200 chars.",
        "",
        "## Runs compared",
        "",
        f"- A: `{meta_a.get('model_slug')}` / `{meta_a.get('run_id')}`",
        f"- B: `{meta_b.get('model_slug')}` / `{meta_b.get('run_id')}`",
        "",
        "## Weighted totals (derived, no winner declared)",
        "",
        f"- weighted_total_a: `{totals['weighted_total_a']}`",
        f"- weighted_total_b: `{totals['weighted_total_b']}`",
        f"- delta_b_minus_a: `{totals['delta_b_minus_a']}`",
        "",
        "## Material category deltas",
        "",
        json.dumps(comparison["material_deltas"], indent=2),
        "",
        "## Per-case objective/behavior scores",
        "",
        "| case_id | A objective | A behavior | B objective | B behavior |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    rules_a = _read_json(run_a / "rule-checks.json").get("cases", {})
    rules_b = _read_json(run_b / "rule-checks.json").get("cases", {})
    case_ids = sorted(set(rules_a) | set(rules_b))
    for case_id in case_ids:
        a = rules_a.get(case_id, {})
        b = rules_b.get(case_id, {})
        lines.append(
            f"| {case_id} | {a.get('objective_score')} | {a.get('behavior_score')} | "
            f"{b.get('objective_score')} | {b.get('behavior_score')} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-a", type=Path, required=True)
    parser.add_argument("--run-b", type=Path, default=None)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "evaluations" / "reports",
    )
    parser.add_argument(
        "--report-a-name",
        default="QWEN3_8B_COBRABENCH_V0_1.md",
    )
    parser.add_argument(
        "--report-b-name",
        default="QWEN3_32B_COBRABENCH_V0_1.md",
    )
    parser.add_argument(
        "--comparison-name",
        default="QWEN3_8B_VS_32B_COMPARISON.md",
    )
    args = parser.parse_args(argv)

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    run_a = args.run_a.resolve()
    report_a = _render_single_report(
        run_a,
        title=f"CobraBench v0.1 Report — {run_a.name}",
    )
    path_a = output_dir / args.report_a_name
    path_a.write_text(
        report_a + f"\n<!-- generated {datetime.now(UTC).isoformat()} -->\n", encoding="utf-8"
    )
    print(path_a)

    if args.run_b is not None:
        run_b = args.run_b.resolve()
        report_b = _render_single_report(
            run_b,
            title=f"CobraBench v0.1 Report — {run_b.name}",
        )
        path_b = output_dir / args.report_b_name
        path_b.write_text(
            report_b + f"\n<!-- generated {datetime.now(UTC).isoformat()} -->\n",
            encoding="utf-8",
        )
        print(path_b)

        comparison = _render_comparison_report(run_a, run_b, title="CobraBench v0.1 Comparison")
        path_cmp = output_dir / args.comparison_name
        path_cmp.write_text(
            comparison + f"\n<!-- generated {datetime.now(UTC).isoformat()} -->\n",
            encoding="utf-8",
        )
        print(path_cmp)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
