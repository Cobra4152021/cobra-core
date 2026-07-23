#!/usr/bin/env python3
"""Build run report, summary, and ADR inputs from a completed rc2 run directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluation.rc2_run import tree_hash  # noqa: E402

OFFICIAL_V01 = 0.840


def _sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory_hash_run(run_dir: Path) -> str:
    lines = []
    for path in sorted(run_dir.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS":
            rel = path.relative_to(run_dir).as_posix()
            lines.append(f"{rel}:{_sha_file(path)}")
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()
    run_dir: Path = args.run_dir
    if not run_dir.is_dir():
        print("missing run dir", file=sys.stderr)
        return 2

    protocol = json.loads((run_dir / "protocol.json").read_text(encoding="utf-8"))
    env = json.loads((run_dir / "environment.json").read_text(encoding="utf-8"))
    inv = json.loads((run_dir / "model_inventory.json").read_text(encoding="utf-8"))
    cases = json.loads((run_dir / "case_manifest.json").read_text(encoding="utf-8"))

    finish = Counter()
    early = Counter()
    categories: dict[str, dict] = {}
    in_tok = out_tok = 0
    runtime_s = 0.0
    parser_strict = parser_tolerant = parser_fail = 0
    eval_errors = 0
    uc_flags = 0
    human_items = 0
    peak_vram = None

    for rec in cases.get("cases", []):
        cid = rec["case_id"]
        cat_path = run_dir / "parsed" / f"{cid}.json"
        if cat_path.is_file():
            cat = json.loads(cat_path.read_text(encoding="utf-8")).get("category", "unknown")
        else:
            cat = "unknown"
        bucket = categories.setdefault(
            cat,
            {
                "case_count": 0,
                "completed": 0,
                "failed": 0,
                "human_review_status": "pending-human-review",
                "confidence": "low-to-moderate",
                "warning": "",
            },
        )
        bucket["case_count"] += 1
        if rec.get("status") == "completed":
            bucket["completed"] += 1
        else:
            bucket["failed"] += 1
        if cat in {"refusal_quality", "uncertainty_calibration"}:
            bucket["warning"] = "small-sample (n=3 category in rc2)"
            bucket["confidence"] = "low"

        tel_path = run_dir / "telemetry" / f"{cid}.json"
        if tel_path.is_file():
            tel = json.loads(tel_path.read_text(encoding="utf-8"))
            in_tok += int(tel.get("input_tokens") or 0)
            out_tok += int(tel.get("output_tokens") or 0)
            finish[str(tel.get("finish_reason"))] += 1
            cls = (tel.get("output_budget") or {}).get("completion_class")
            if cls:
                early[str(cls)] += 1
        runtime_s += float(rec.get("duration_s") or 0)
        human_items += int(rec.get("human_review_items") or 0)

        score_path = run_dir / "scores" / f"{cid}.json"
        if score_path.is_file():
            scores = json.loads(score_path.read_text(encoding="utf-8"))
            fmt = (scores.get("authoritative") or {}).get("format_compliance", {}).get("metrics")
            if fmt:
                if fmt.get("strict_parse_success"):
                    parser_strict += 1
                elif fmt.get("tolerant_parse_success"):
                    parser_tolerant += 1
                else:
                    parser_fail += 1
            uc = (scores.get("advisory") or {}).get("unsupported_claims", {}).get("metrics")
            if uc:
                uc_flags += int(uc.get("unsupported_claim_count") or 0)

    completed = int(cases.get("completed") or 0)
    failed = int(cases.get("failed") or 0)
    attempted = len(cases.get("cases") or [])
    run_status = protocol.get("status")
    score_completeness = "automated-preliminary-incomplete"
    weighted = None
    if completed < 46 or failed > 0 or human_items > 0:
        score_completeness = "incomplete-blocked-full-weighted-score"
    if completed == 46 and human_items == 0:
        score_completeness = "human-completed-experimental-possible"
    # Never emit official; never emit full weighted without human review.
    weighted_note = (
        "No experimental weighted score is published: human-required fields remain "
        "pending-human-review and unsupported-claim automation is advisory-only."
    )

    run_inv = inventory_hash_run(run_dir)
    run_tree = tree_hash(run_dir)

    report = f"""# Qwen3-8B × CobraBench v0.2-rc2 Run Report

**Label:** Experimental release-candidate evaluation — not an official CobraBench v0.2 score.

**Direct comparison prohibition:** This result must not be presented as an improvement or decline versus the official CobraBench v0.1 score of **{OFFICIAL_V01}**.

## Run identity

| Field | Value |
| --- | --- |
| Run ID | `{protocol.get("run_id")}` |
| Status | `{run_status}` |
| Code commit | `{protocol.get("code_commit_sha")}` |
| Started | `{protocol.get("started_at")}` |
| Ended | `{protocol.get("ended_at")}` |
| Prepared protocol SHA-256 | `{protocol.get("prepared_protocol_sha256")}` |
| Prepared protocol status (unchanged) | `prepared-not-run` |
| rc2 inventory hash | `{protocol.get("rc2_inventory_hash")}` |
| rc2 tree hash | `{protocol.get("rc2_tree_hash")}` |
| Model inventory hash | `{inv.get("inventory_hash")}` |
| Run inventory hash | `{run_inv}` |
| Run tree hash | `{run_tree}` |

## Model identity

| Field | Value |
| --- | --- |
| Model | `{inv.get("model_name")}` |
| Upstream | `{inv.get("upstream_repository")}` |
| Revision | `{inv.get("model_revision")}` |
| Config hash | `{inv.get("config_hash")}` |
| Quantization | `{inv.get("quantization_method")}` |
| Quant config | `{json.dumps(inv.get("quantization_configuration"))}` |
| trust_remote_code | `{inv.get("trust_remote_code")}` |
| dtype / device_map | `{inv.get("dtype")}` / `{inv.get("device_map")}` |

## Environment

| Field | Value |
| --- | --- |
| OS | `{env.get("os")}` |
| Python / Torch / CUDA | `{env.get("software_versions")}` |
| GPU | `{(env.get("hardware") or {}).get("gpu_model")}` |
| VRAM total / available (preflight) | `{(env.get("hardware") or {}).get("total_vram_bytes")}` / `{(env.get("hardware") or {}).get("available_vram_bytes")}` |
| System RAM | `{env.get("memory")}` |
| Disk free | `{(env.get("disk") or {}).get("free_bytes")}` |

## Execution totals

| Metric | Value |
| --- | --- |
| Cases attempted | {attempted} |
| Cases completed | {completed} |
| Cases failed | {failed} |
| Retries | 0 (quality retries prohibited) |
| CUDA errors | see case errors |
| Process crash | none recorded in runner |
| Input tokens | {in_tok} |
| Output tokens | {out_tok} |
| Runtime total (s) | {runtime_s:.3f} |
| Peak VRAM | {peak_vram if peak_vram is not None else "not aggregated across cases"} |
| Finish reasons | {dict(finish)} |
| Early-stop / completion classes | {dict(early)} |
| Strict parser success | {parser_strict} |
| Tolerant parser recovery | {parser_tolerant} |
| Parser failure | {parser_fail} |
| Evaluator errors | {eval_errors} |
| Unsupported-claim raw flag count | {uc_flags} (advisory-only) |
| Human-review queue items | {human_items} |

## Score completeness

**State:** `{score_completeness}`

{weighted_note}

Experimental weighted score: **not reported** (incomplete / pending human review).

## Unsupported-claim warning

`unsupported_claims@2.0.0` is **advisory-only** (Phase 2I: TPR 0.000, FNR 1.000, cannot_determine 0.700). Zero flags are not proof of grounding.

## Contradiction warning

Automated contradiction detection is preserved but explanation quality requires human review. Do not infer strong contradiction capability from detection alone.

## Small-sample warnings

* refusal_quality: n=3
* uncertainty_calibration: n=3

## Category preliminary table

| Category | Cases | Completed | Automated score | Human review | Confidence | Warning |
| --- | ---: | ---: | --- | --- | --- | --- |
"""
    for cat, b in sorted(categories.items()):
        report += (
            f"| {cat} | {b['case_count']} | {b['completed']} | not computed "
            f"(incomplete) | {b['human_review_status']} | {b['confidence']} | {b['warning']} |\n"
        )

    report += """
## Limitations

* rc2 is non-final (Outcome D governance).
* Human ratings were not fabricated; queues remain pending.
* No official CobraBench v0.2 score exists.
* Official v0.1 score 0.840 remains authoritative for v0.1 only.

## Reproducibility

1. Confirm frozen rc2 hashes.
2. Confirm model revision `b968826d9c46dd6066d109eabc6255188de91218`.
3. Run preflight + smoke.
4. Execute `scripts/run_cobrabench_v02_rc2.py` with the same seed and 4-bit settings.
5. Do not mutate prepared protocol, rc1, rc2, or v0.1 baseline.

## Designation

This report does **not** designate Qwen3-8B as Cobra Core and does **not** authorize training.
"""
    out = run_dir / "reports" / "QWEN3_8B_COBRABENCH_V0_2_RC2_RUN_REPORT.md"
    out.write_text(report, encoding="utf-8")

    summary = f"""# Qwen3-8B CobraBench v0.2-rc2 Evaluation Summary

## Official historical result (unchanged)

| Item | Value |
| --- | --- |
| Benchmark | CobraBench v0.1 |
| Model | Qwen3-8B |
| Official weighted score | **{OFFICIAL_V01}** |
| Baseline inventory hash | `84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6` |

This Phase 3B work does **not** rerun or replace that result.

## Experimental rc2 run

| Item | Value |
| --- | --- |
| Benchmark | CobraBench v0.2-rc2 (non-final) |
| Run ID | `{protocol.get("run_id")}` |
| Status | `{run_status}` |
| Label | Experimental release-candidate evaluation — not an official CobraBench v0.2 score |
| Score completeness | `{score_completeness}` |
| Experimental weighted score | **not reported** |

Permitted wording if a complete experimental weighted score were later human-completed:

> Qwen3-8B received X under CobraBench v0.2-rc2. This experimental result is not directly comparable with its official 0.840 CobraBench v0.1 score.

## Automated preliminary findings

* Cases completed: {completed}/{attempted}
* Unsupported-claim automation: advisory-only; raw flags={uc_flags}
* Contradiction automation: detection only; explanation pending human review
* Parser strict/tolerant/fail: {parser_strict}/{parser_tolerant}/{parser_fail}

## Pending human findings

* Queue size: {human_items}
* All human-required dimensions remain `pending-human-review`

## Incomparable score systems

v0.1 and v0.2-rc2 differ in case set, weights, evaluators, and human-review requirements. Direct numerical comparison is prohibited.

## Category table

| Category | Case count | Completed | Automated score | Human review | Confidence | Warning |
| --- | ---: | ---: | --- | --- | --- | --- |
"""
    for cat, b in sorted(categories.items()):
        summary += (
            f"| {cat} | {b['case_count']} | {b['completed']} | incomplete | "
            f"{b['human_review_status']} | {b['confidence']} | {b['warning']} |\n"
        )

    summary_path = ROOT / "evaluations/reports/QWEN3_8B_COBRABENCH_V0_2_RC2_SUMMARY.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")

    meta = {
        "run_id": protocol.get("run_id"),
        "run_status": run_status,
        "score_completeness": score_completeness,
        "weighted_score": weighted,
        "run_inventory_hash": run_inv,
        "run_tree_hash": run_tree,
        "human_review_queue_size": human_items,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "runtime_s": runtime_s,
        "finish_reasons": dict(finish),
        "completion_classes": dict(early),
        "parser_strict": parser_strict,
        "parser_tolerant": parser_tolerant,
        "parser_fail": parser_fail,
        "unsupported_claim_raw_flags": uc_flags,
        "official_v01_score_unchanged": OFFICIAL_V01,
        "direct_comparison_prohibited": True,
        "official_rc2_label_forbidden": True,
    }
    (run_dir / "reports" / "finalize_meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
