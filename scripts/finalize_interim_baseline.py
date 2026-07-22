#!/usr/bin/env python3
"""Aggregate Qwen3-8B interim baseline scores and write reports/ADR drafts."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.benchmarks.release import load_release_cases  # noqa: E402
from cobra_core.schemas.categories import CATEGORY_WEIGHTS  # noqa: E402


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.fmean(values))


def _p90(values: list[float]) -> float | None:
    if len(values) < 5:
        return None
    ordered = sorted(values)
    idx = int(round(0.9 * (len(ordered) - 1)))
    return float(ordered[idx])


def aggregate(run_dir: Path) -> dict[str, Any]:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    objective = json.loads((run_dir / "objective-metrics.json").read_text(encoding="utf-8"))
    rules = json.loads((run_dir / "rule-checks.json").read_text(encoding="utf-8"))
    human = json.loads((run_dir / "human-scores.json").read_text(encoding="utf-8"))
    errors = json.loads((run_dir / "errors.json").read_text(encoding="utf-8"))
    cases = {c.case_id: c for c in load_release_cases("0.1")}

    human_by_id = {item["case_id"]: item for item in human.get("scores", [])}
    latencies: list[float] = []
    tps: list[float] = []
    in_tokens = 0
    out_tokens = 0
    ok = 0
    failed = 0
    hallu = Counter()
    cite_prec: list[float] = []
    cite_cov: list[float] = []
    fab_cites = 0
    unsupported = 0
    by_cat_scores: dict[str, list[float]] = defaultdict(list)

    for summary in run.get("cases", []):
        cid = summary["case_id"]
        case = cases[cid]
        if summary.get("status") == "ok":
            ok += 1
            if summary.get("latency_ms") is not None:
                latencies.append(float(summary["latency_ms"]))
            if summary.get("tokens_per_second") is not None:
                tps.append(float(summary["tokens_per_second"]))
            in_tokens += int(summary.get("input_token_count") or 0)
            out_tokens += int(summary.get("output_token_count") or 0)
        else:
            failed += 1

        obj = objective.get("cases", {}).get(cid, {})
        hum = human_by_id.get(cid)
        score = float(hum["score"]) if hum else float(obj.get("objective_score") or 0.0)
        by_cat_scores[case.category.value].append(score)

        hall = (obj.get("hallucination") or {}).get("severity") or "H0"
        hallu[str(hall)] += 1
        cm = obj.get("citation_metrics") or {}
        if cm.get("citation_precision") is not None:
            cite_prec.append(float(cm["citation_precision"]))
        if cm.get("citation_coverage") is not None:
            cite_cov.append(float(cm["citation_coverage"]))
        fab_cites += int(cm.get("fabricated_citation_count") or 0)
        unsupported += int(cm.get("unsupported_claim_count") or 0)

    category_means = {
        cat: (sum(vals) / len(vals) if vals else None) for cat, vals in by_cat_scores.items()
    }
    weighted = 0.0
    weight_sum = 0.0
    for cat, weight in CATEGORY_WEIGHTS.items():
        val = category_means.get(cat.value)
        if val is None:
            continue
        weighted += val * weight
        weight_sum += weight
    overall = weighted / weight_sum if weight_sum else None

    return {
        "run_id": run.get("run_id"),
        "generated_at": datetime.now(UTC).isoformat(),
        "cases_attempted": len(run.get("cases", [])),
        "cases_completed": ok,
        "cases_failed": failed,
        "errors": errors.get("errors", []),
        "category_scores": category_means,
        "overall_interim_weighted_score": overall,
        "citation": {
            "precision_mean": _mean(cite_prec),
            "coverage_mean": _mean(cite_cov),
            "fabricated_citation_count": fab_cites,
            "unsupported_claim_count": unsupported,
        },
        "hallucination_severity_distribution": dict(hallu),
        "latency_ms": {
            "median": _median(latencies),
            "mean": _mean(latencies),
            "p90": _p90(latencies),
        },
        "tokens_per_second": {"median": _median(tps), "mean": _mean(tps)},
        "tokens": {"input_total": in_tokens, "output_total": out_tokens},
        "human_coverage": human.get("coverage"),
        "judge_status": "not_run",
        "rule_case_count": len(rules.get("cases", {})),
        "objective_case_count": len(objective.get("cases", {})),
    }


def write_report(agg: dict[str, Any], run_dir: Path, out_path: Path) -> None:
    cats = agg["category_scores"]
    lines = [
        "# Qwen3-8B — CobraBench v0.1 Interim Baseline Report",
        "",
        "**Status:** Interim baseline complete (single-model).",
        "**Label:** Qwen3-8B CobraBench v0.1 interim baseline score",
        "**Not Cobra Core.** Results do not establish Qwen3-32B performance.",
        "",
        "## Executive summary",
        "",
        f"- Cases attempted: {agg['cases_attempted']}",
        f"- Cases completed: {agg['cases_completed']}",
        f"- Cases failed: {agg['cases_failed']}",
        f"- Overall interim weighted score: {agg['overall_interim_weighted_score']:.4f}"
        if agg["overall_interim_weighted_score"] is not None
        else "- Overall interim weighted score: unavailable",
        f"- Human review coverage: {agg.get('human_coverage')}",
        f"- LLM-as-judge: {agg['judge_status']}",
        f"- Run directory: `{run_dir}`",
        "",
        "## Model and protocol",
        "",
        "| Field | Value |",
        "| --- | --- |",
        "| Model | Qwen/Qwen3-8B |",
        "| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |",
        "| Benchmark | CobraBench v0.1 |",
        "| Thinking | disabled |",
        "| Temperature / seed | 0.0 / 123 |",
        "| max_new_tokens | 512 |",
        "| Precision | bitsandbytes 4-bit NF4 on official BF16 |",
        "| Protocol | `evaluations/protocols/qwen3-8b-cobrabench-v0.1.json` |",
        "",
        "## Category-level scores",
        "",
        "| Category | Weight | Score |",
        "| --- | ---: | ---: |",
    ]
    for cat, weight in CATEGORY_WEIGHTS.items():
        val = cats.get(cat.value)
        lines.append(f"| {cat.value} | {weight:.2f} | {'n/a' if val is None else f'{val:.4f}'} |")
    cite = agg["citation"]
    lat = agg["latency_ms"]
    tps = agg["tokens_per_second"]
    lines.extend(
        [
            "",
            "## Citation metrics",
            "",
            f"- Precision (mean): {cite['precision_mean']}",
            f"- Coverage (mean): {cite['coverage_coverage'] if 'coverage_coverage' in cite else cite['coverage_mean']}",
            f"- Fabricated citation count: {cite['fabricated_citation_count']}",
            f"- Unsupported claim count (heuristic): {cite['unsupported_claim_count']}",
            "",
            "## Hallucination severity distribution (automated layer)",
            "",
            "```json",
            json.dumps(agg["hallucination_severity_distribution"], indent=2),
            "```",
            "",
            "## Latency and throughput",
            "",
            f"- Median latency ms: {lat['median']}",
            f"- Mean latency ms: {lat['mean']}",
            f"- P90 latency ms: {lat['p90']}",
            f"- Median tok/s: {tps['median']}",
            f"- Mean tok/s: {tps['mean']}",
            f"- Total input tokens: {agg['tokens']['input_total']}",
            f"- Total output tokens: {agg['tokens']['output_total']}",
            "",
            "## Failures",
            "",
            "```json",
            json.dumps(agg["errors"], indent=2),
            "```",
            "",
            "## Limitations",
            "",
            "- Single-model interim baseline; no Qwen3-32B comparison.",
            "- Human scores are structured reviewer judgments assisted by objective/rule layers; not a multi-rater study.",
            "- Automated unsupported-claim detection is heuristic, not definitive hallucination proof.",
            "- Load-time 4-bit differs from native BF16.",
            "",
            "## Recommended next phase (requires authorization)",
            "",
            "- Weakness analysis on recurring failure modes, or",
            "- Thinking-mode cohort, or",
            "- Suitable hardware for Qwen3-32B evaluation.",
            "",
            "Do not begin fine-tuning without separate authorization.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument(
        "--report",
        type=Path,
        default=ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md",
    )
    parser.add_argument(
        "--aggregate-out",
        type=Path,
        default=None,
    )
    args = parser.parse_args(argv)
    agg = aggregate(args.run_dir)
    agg_path = args.aggregate_out or (args.run_dir / "aggregate-summary.json")
    agg_path.write_text(json.dumps(agg, indent=2) + "\n", encoding="utf-8")
    write_report(agg, args.run_dir, args.report)
    print(
        json.dumps(
            {
                "aggregate": str(agg_path),
                "report": str(args.report),
                "overall": agg["overall_interim_weighted_score"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
