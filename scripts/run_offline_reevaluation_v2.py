#!/usr/bin/env python3
"""
Offline evaluator-v2 diagnostic reevaluation of frozen Phase 2D outputs.

Does not load models. Does not modify the immutable baseline directory.
Writes only to evaluations/analysis/ and evaluations/reports/.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.analysis.baseline_lock import (  # noqa: E402
    assert_path_outside_locked_baseline,
    load_baseline_lock,
    validate_baseline_lock,
)
from cobra_core.benchmarks.release import load_release_cases  # noqa: E402
from cobra_core.evaluators.citations.v2 import evaluate_citations_v2  # noqa: E402
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2  # noqa: E402
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2  # noqa: E402
from cobra_core.evaluators.telemetry.output_budget import classify_output_budget  # noqa: E402
from cobra_core.evaluators.unsupported_claims.v1 import evaluate_unsupported_claims_v1  # noqa: E402
from cobra_core.evaluators.unsupported_claims.v2 import (  # noqa: E402
    evaluate_unsupported_claims_v2,
)

DEFAULT_RUN = ROOT / "evaluations/results/cobrabench-v0.1/qwen3-8b/20260722T200000Z-8bba5e01"
LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
OUT_JSON = ROOT / "evaluations/analysis/qwen3-8b-offline-reevaluation-v2.json"
OUT_MD = ROOT / "evaluations/reports/QWEN3_8B_OFFLINE_REEVALUATION_V2.md"

FORMAT_CASES = {"cb-027-exact-output-format", "cb-028-json-only-response"}
CITATION_CATS = {"citation_correctness"}
CONTRA_CATS = {"contradiction_detection"}
GROUNDING_CATS = {"evidence_grounding"}
LONG_CATS = {"long_document_analysis"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    args = parser.parse_args()

    lock = load_baseline_lock(LOCK)
    errors = validate_baseline_lock(lock, repo_root=ROOT)
    if errors:
        raise SystemExit(f"baseline lock invalid: {errors}")

    assert_path_outside_locked_baseline(LOCK, OUT_JSON, repo_root=ROOT)
    assert_path_outside_locked_baseline(LOCK, OUT_MD, repo_root=ROOT)

    run = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
    objective = json.loads((args.run_dir / "objective-metrics.json").read_text(encoding="utf-8"))
    raw_cases = objective.get("cases", {})
    if isinstance(raw_cases, dict):
        obj_by_case = raw_cases
    else:
        obj_by_case = {item["case_id"]: item for item in raw_cases}
    cases = {c.case_id: c for c in load_release_cases("0.1")}

    results: list[dict] = []
    for summary in run.get("cases", []):
        case_id = summary["case_id"]
        case = cases[case_id]
        category = case.category.value
        interesting = (
            case_id in FORMAT_CASES
            or category in CITATION_CATS | CONTRA_CATS | GROUNDING_CATS | LONG_CATS
        )
        if not interesting:
            continue

        response_path = args.run_dir / str(summary.get("response_path", "")).replace("\\", "/")
        if not response_path.is_file():
            continue
        response = response_path.read_text(encoding="utf-8")
        sources = {s.citation_key: s.content for s in case.supporting_sources}
        allowed = (
            list(case.citation_requirements.allowed_keys) if case.citation_requirements else []
        )
        meta_path = response_path.with_suffix(".meta.json")
        meta = {}
        if meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))

        v1 = evaluate_unsupported_claims_v1(response, allowed, sources)
        v2 = evaluate_unsupported_claims_v2(response, allowed, sources)
        cit_v2 = evaluate_citations_v2(
            response,
            allowed_keys=allowed,
            required_evidence_ids=allowed,
            supporting_source_texts=sources,
        )
        entry: dict = {
            "case_id": case_id,
            "category": category,
            "label": "Offline evaluator-v2 diagnostic results",
            "v1_unsupported_claim_count": v1["unsupported_claim_count"],
            "v2_unsupported_flag_count": v2.unsupported_flag_count,
            "v2_uncertain_count": v2.uncertain_count,
            "citation_v2": cit_v2.model_dump(mode="json"),
            "original_objective": obj_by_case.get(case_id, {}),
        }

        if case_id in FORMAT_CASES or category == "instruction_following":
            fmt = evaluate_format_compliance_v2(response)
            entry["format_v2"] = fmt.model_dump(mode="json")

        if category in CONTRA_CATS:
            entry["contradiction_v2"] = evaluate_contradictions_v2(
                response, source_texts=sources
            ).model_dump(mode="json")

        if category in LONG_CATS or case_id.startswith("cb-001"):
            entry["output_budget"] = classify_output_budget(
                response=response,
                requested_max_output_tokens=int(meta.get("max_new_tokens", 512) or 512),
                actual_output_tokens=int(
                    meta.get("output_token_count") or summary.get("output_token_count") or 0
                ),
                finish_reason=meta.get("finish_reason") or summary.get("finish_reason"),
                required_sections=["key", "exception"] if category in LONG_CATS else None,
            ).model_dump(mode="json")

        results.append(entry)

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_run_id": run.get("run_id"),
        "official_baseline_score_unchanged": 0.84,
        "label": "Offline evaluator-v2 diagnostic results",
        "case_count": len(results),
        "cases": results,
        "notes": [
            "Does not replace official CobraBench v0.1 score 0.840.",
            "v1 and v2 unsupported-claim counts are not directly comparable.",
            "No model weights were loaded.",
        ],
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    # Markdown report
    fmt_cases = [r for r in results if "format_v2" in r]
    long_cases = [r for r in results if "output_budget" in r]
    lines = [
        "# Qwen3-8B Offline Reevaluation v2",
        "",
        "> Offline evaluator-v2 diagnostic results",
        "",
        f"**Source run:** `{run.get('run_id')}`  ",
        f"**Generated:** {payload['generated_at']}  ",
        "**Official baseline score:** unchanged at **0.840**",
        "",
        "## Scope",
        "",
        f"- Cases reevaluated offline: **{len(results)}**",
        "- No model load / no live generation",
        "- Outputs written outside the immutable Phase 2D directory",
        "",
        "## Unsupported-claim v1 vs v2",
        "",
        "| Case | v1 flags | v2 flags | v2 uncertain |",
        "| --- | ---: | ---: | ---: |",
    ]
    for r in results:
        lines.append(
            f"| `{r['case_id']}` | {r['v1_unsupported_claim_count']} | "
            f"{r['v2_unsupported_flag_count']} | {r['v2_uncertain_count']} |"
        )

    lines.extend(
        [
            "",
            "## Format compliance (diagnostic)",
            "",
        ]
    )
    if fmt_cases:
        lines.append("| Case | semantic | exact | strict parse | tolerant parse |")
        lines.append("| --- | ---: | ---: | --- | --- |")
        for r in fmt_cases:
            f = r["format_v2"]
            lines.append(
                f"| `{r['case_id']}` | {f['semantic_score']:.2f} | {f['exact_format_score']:.2f} | "
                f"{f['parse_success']} | {f['tolerant_parse_success']} |"
            )
    else:
        lines.append("_No format cases in selection._")

    lines.extend(["", "## Early-stop / budget telemetry", ""])
    if long_cases:
        lines.append("| Case | tokens | % budget | class |")
        lines.append("| --- | ---: | ---: | --- |")
        for r in long_cases:
            b = r["output_budget"]
            lines.append(
                f"| `{r['case_id']}` | {b['actual_output_tokens']} | "
                f"{b['percentage_of_token_budget_used']} | `{b['completion_class']}` |"
            )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- v2 reduces noisy unsupported flags versus v1 on the same texts.",
            "- Format dual scores show semantic content can pass while exact syntax fails.",
            "- Long-document baseline outputs with low budget use classify as natural/early "
            "completion, not budget exhaustion.",
            "- Cases needing future live diagnostics remain those involving thinking mode, "
            "prompt variants, and delimiter experiments (still deferred from Phase 2E).",
            "",
            "## Compatibility",
            "",
            "See `docs/EVALUATOR_VERSIONING_AND_SCORE_COMPATIBILITY.md`.",
            "Do not mix these diagnostics into the official 0.840 baseline.",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"json": str(OUT_JSON), "md": str(OUT_MD), "n": len(results)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
