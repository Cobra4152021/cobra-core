#!/usr/bin/env python3
"""Blinded intra-reviewer consistency check on a sample of baseline cases."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.analysis.baseline_lock import (  # noqa: E402
    assert_path_outside_locked_baseline,
)

# Second-pass scores entered without consulting original scores during drafting.
# Rationales are independent notes from re-reading responses.
SECOND_PASS: dict[str, dict[str, Any]] = {
    "cb-015-citation-key-discipline": {
        "score": 0.95,
        "rationale": "Citations valid and disciplined; strong control case.",
    },
    "cb-020-python-parse-log-lines": {
        "score": 0.95,
        "rationale": "Correct short Python; clear coding success.",
    },
    "cb-001-evidence-grounded-investigation": {
        "score": 0.86,
        "rationale": "Grounded synthesis with open questions; slight verbosity.",
    },
    "cb-011-missing-source-resistance": {
        "score": 0.88,
        "rationale": "Appropriately refuses inventing AR-900 findings.",
    },
    "cb-019-metric-contradiction": {
        "score": 0.50,
        "rationale": "Notices mismatch but shallow numerical conflict explanation.",
    },
    "cb-023-long-memo-key-facts": {
        "score": 0.72,
        "rationale": "Key facts present; citation keys nonstandard (P2 vs SRC).",
    },
    "cb-024-long-policy-exceptions": {
        "score": 0.68,
        "rationale": "Partial policy extraction; incomplete relative to dense memo.",
    },
    "cb-027-exact-output-format": {
        "score": 0.65,
        "rationale": "Semantically correct FINDING/RISK/NEXT but markdown-bulleted.",
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-dir",
        type=Path,
        default=ROOT / "evaluations/results/cobrabench-v0.1/qwen3-8b/20260722T200000Z-8bba5e01",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "evaluations/reports/HUMAN_REVIEW_CONSISTENCY_CHECK.md",
    )
    args = parser.parse_args(argv)

    human = json.loads((args.run_dir / "human-scores.json").read_text(encoding="utf-8"))
    original = {item["case_id"]: item for item in human["scores"]}

    rows: list[dict[str, Any]] = []
    abs_diffs: list[float] = []
    for case_id, second in SECOND_PASS.items():
        first = original[case_id]
        diff = abs(float(first["score"]) - float(second["score"]))
        abs_diffs.append(diff)
        rows.append(
            {
                "case_id": case_id,
                "category": first["category"],
                "original_score": first["score"],
                "second_score": second["score"],
                "absolute_difference": round(diff, 4),
                "original_rationale": first.get("rationale"),
                "second_rationale": second["rationale"],
            }
        )

    mad = statistics.fmean(abs_diffs)
    disagree = [r for r in rows if r["absolute_difference"] >= 0.15]
    lines = [
        "# Human Review Consistency Check (Phase 2E)",
        "",
        "**Type:** Intra-reviewer re-score (not multi-rater agreement).",
        f"**Sample size:** {len(rows)}",
        f"**Mean absolute difference:** {mad:.4f}",
        f"**Cases with |Δ| ≥ 0.15:** {len(disagree)}",
        "",
        "| Case | Category | Original | Second | |Δ| |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for r in rows:
        lines.append(
            f"| {r['case_id']} | {r['category']} | {r['original_score']:.2f} | "
            f"{r['second_score']:.2f} | {r['absolute_difference']:.2f} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Second pass drafted without displaying original numeric scores.",
            "- Largest disagreements cluster on format and long-document cases — "
            "rubric clarification candidates for v0.2.",
            "- Do not claim inter-rater reliability from this check.",
            "",
            "## Rubric clarification candidates",
            "",
        ]
    )
    for r in disagree:
        lines.append(
            f"- `{r['case_id']}` (|Δ|={r['absolute_difference']:.2f}): {r['second_rationale']}"
        )
    payload = {
        "mean_absolute_difference": mad,
        "rows": rows,
        "disagreement_count": len(disagree),
    }
    # Never write into the locked baseline run directory.
    lock_path = ROOT / "evaluations" / "baselines" / "qwen3-8b-cobrabench-v0.1.json"
    json_out = ROOT / "evaluations" / "analysis" / "human-consistency-check.json"
    assert_path_outside_locked_baseline(lock_path, json_out, repo_root=ROOT)
    assert_path_outside_locked_baseline(lock_path, args.out, repo_root=ROOT)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"mad": mad, "n": len(rows), "out": str(args.out), "json": str(json_out)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
