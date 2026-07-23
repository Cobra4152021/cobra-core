#!/usr/bin/env python3
"""Build the unsupported-claims v2 gold audit fixture from Phase 2D outputs (read-only)."""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.analysis.baseline_lock import assert_path_outside_locked_baseline  # noqa: E402
from cobra_core.benchmarks.release import load_release_cases  # noqa: E402
from cobra_core.evaluators.unsupported_claims.v1 import evaluate_unsupported_claims_v1  # noqa: E402
from cobra_core.evaluators.unsupported_claims.v2 import (  # noqa: E402
    evaluate_unsupported_claims_v2,
)

_spec = importlib.util.spec_from_file_location(
    "audit_unsupported_claims",
    ROOT / "scripts" / "audit_unsupported_claims.py",
)
assert _spec and _spec.loader
_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_audit)
extract_flags = _audit.extract_flags

DEFAULT_RUN = ROOT / "evaluations/results/cobrabench-v0.1/qwen3-8b/20260722T200000Z-8bba5e01"
OUT_DIR = ROOT / "evaluations/fixtures/unsupported-claims-v2"
LOCK = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"

_LABEL_MAP = {
    "supported_paraphrase": ("evidence_paraphrase", "directly_supported", False),
    "harmless_connective": ("connective_language", "not_applicable", False),
    "inference_clearly_labeled": (
        "explicitly_labeled_inference",
        "reasonable_labeled_inference",
        False,
    ),
    "instruction_text_mistaken": ("instruction_repetition", "not_applicable", False),
    "evidence_matching_failure": ("unknown", "cannot_determine", False),
    "uncertain": ("unknown", "cannot_determine", False),
    "true_unsupported_claim": ("unsupported_candidate", "unsupported", True),
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-sample", type=int, default=50)
    args = parser.parse_args()

    assert_path_outside_locked_baseline(LOCK, OUT_DIR / "fixtures.json", repo_root=ROOT)

    run = json.loads((args.run_dir / "run.json").read_text(encoding="utf-8"))
    cases = {c.case_id: c for c in load_release_cases("0.1")}
    rng = random.Random(args.seed)

    pool: list[dict] = []
    citation_hallucination: list[dict] = []

    for summary in run.get("cases", []):
        case_id = summary["case_id"]
        case = cases[case_id]
        response_path = args.run_dir / str(summary.get("response_path", "")).replace("\\", "/")
        if not response_path.is_file():
            continue
        response = response_path.read_text(encoding="utf-8")
        sources = {s.citation_key: s.content for s in case.supporting_sources}
        allowed = (
            list(case.citation_requirements.allowed_keys) if case.citation_requirements else []
        )
        flags = extract_flags(response, allowed, sources, case_id=case_id)
        for flag in flags:
            item = {
                "case_id": case_id,
                "category": case.category.value,
                "sentence": flag["sentence"],
                "cited_keys": [k for k in flag["cited_keys"].split(",") if k],
                "evidence_excerpt": " | ".join(
                    f"[{k}] {sources.get(k, '')[:160]}" for k in list(sources)[:2]
                ),
                "original_v1_flag": True,
                "audited_label": flag["label"],
            }
            if case.category.value in {"citation_correctness", "hallucination_resistance"}:
                citation_hallucination.append(item)
            else:
                pool.append(item)

    rng.shuffle(pool)
    selected = citation_hallucination[:]
    need = max(0, args.min_sample - len(selected))
    selected.extend(pool[:need])
    selected = selected[: max(args.min_sample, len(selected))]

    fixtures = []
    for idx, item in enumerate(selected, start=1):
        label = item["audited_label"]
        claim_class, support_state, expect_flag = _LABEL_MAP.get(
            label, ("unknown", "cannot_determine", False)
        )
        fixtures.append(
            {
                "fixture_id": f"uc-v2-{idx:03d}",
                "case_id": item["case_id"],
                "category": item["category"],
                "output_excerpt": item["sentence"],
                "evidence_excerpt": item["evidence_excerpt"],
                "original_v1_flag": True,
                "audited_classification": claim_class,
                "audited_support_state": support_state,
                "audited_should_flag_unsupported": expect_flag,
                "rationale": f"Phase 2E audit label={label}",
                "expected_v2": {
                    "claim_class": claim_class,
                    "support_state": support_state,
                    "flagged_as_unsupported": expect_flag,
                },
            }
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures_path = OUT_DIR / "fixtures.json"
    fixtures_path.write_text(
        json.dumps(
            {
                "fixture_set": "unsupported-claims-v2",
                "source_run_id": run.get("run_id"),
                "generated_at": datetime.now(UTC).isoformat(),
                "count": len(fixtures),
                "notes": (
                    "Synthetic/public baseline excerpts only. "
                    "Gold labels from Phase 2E audit. Offline diagnostic use."
                ),
                "fixtures": fixtures,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    tp = fp = tn = fn = 0
    class_match = 0
    uncertain = 0
    for fix in fixtures:
        case = cases[fix["case_id"]]
        sources = {s.citation_key: s.content for s in case.supporting_sources}
        allowed = (
            list(case.citation_requirements.allowed_keys) if case.citation_requirements else []
        )
        result = evaluate_unsupported_claims_v2(fix["output_excerpt"], allowed, sources)
        span = result.spans[0] if result.spans else None
        pred_flag = bool(span and span.flagged_as_unsupported)
        gold_flag = bool(fix["audited_should_flag_unsupported"])
        if pred_flag and gold_flag:
            tp += 1
        elif pred_flag and not gold_flag:
            fp += 1
        elif (not pred_flag) and (not gold_flag):
            tn += 1
        else:
            fn += 1
        if span and span.claim_class.value == fix["audited_classification"]:
            class_match += 1
        uncertain += result.uncertain_count

    predicted_pos = tp + fp
    labeled_neg = tn + fp
    precision = tp / predicted_pos if predicted_pos else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    fpr = fp / labeled_neg if labeled_neg else 0.0

    v1_flags = 0
    for fix in fixtures:
        case = cases[fix["case_id"]]
        sources = {s.citation_key: s.content for s in case.supporting_sources}
        allowed = (
            list(case.citation_requirements.allowed_keys) if case.citation_requirements else []
        )
        if (
            evaluate_unsupported_claims_v1(fix["output_excerpt"], allowed, sources)[
                "unsupported_claim_count"
            ]
            > 0
        ):
            v1_flags += 1

    metrics = {
        "fixture_count": len(fixtures),
        "v1_flagged_in_sample": v1_flags,
        "v1_false_positive_rate_on_audit_sample": 1.0,
        "v2": {
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(fpr, 4),
            "classification_match_rate": round(class_match / len(fixtures), 4) if fixtures else 0.0,
            "uncertain_rate": round(uncertain / max(1, len(fixtures)), 4),
        },
        "acceptance": {
            "fpr_below_v1": fpr < 1.0,
            "materially_outperforms_v1": fpr < 0.25,
            "notes": (
                "Gold labels are nearly all non-unsupported (Phase 2E audit). "
                "v2 should avoid flagging paraphrases/structural text."
            ),
        },
        "generated_at": datetime.now(UTC).isoformat(),
    }
    metrics_path = OUT_DIR / "metrics.json"
    assert_path_outside_locked_baseline(LOCK, metrics_path, repo_root=ROOT)
    metrics_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"fixtures": str(fixtures_path), "metrics": metrics}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
