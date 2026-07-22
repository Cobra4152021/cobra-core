#!/usr/bin/env python3
"""
Bounded Phase 2E diagnostic generations for Qwen3-8B.

Writes under evaluations/results/diagnostics/ (NOT official CobraBench v0.1).
Does not overwrite the locked baseline run.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.analysis.baseline_lock import assert_baseline_not_overwritten  # noqa: E402
from cobra_core.benchmarks.release import load_release_cases  # noqa: E402
from cobra_core.evaluation.cobrabench_run import build_user_prompt  # noqa: E402
from cobra_core.inference.engine import LocalInferenceEngine  # noqa: E402
from cobra_core.providers.qwen_local import QwenLocalAdapter  # noqa: E402
from cobra_core.schemas.inference import InferenceRequest  # noqa: E402
from cobra_core.schemas.manifest import ModelManifest  # noqa: E402

BASELINE_RUN = "20260722T200000Z-8bba5e01"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _clarified_format_prompt(case: Any) -> str:
    base = build_user_prompt(case)
    return (
        base
        + "\nFORMAT RULES (exact):\n"
        + "FINDING: <one line>\n"
        + "RISK: <one line>\n"
        + "NEXT: <one line>\n"
        + "Use those three labels exactly, with a colon, and no markdown bolding.\n"
    )


def _schema_format_prompt(case: Any) -> str:
    base = build_user_prompt(case)
    return (
        base
        + "\nReturn exactly this schema with no other text:\n"
        + "FINDING: ...\nRISK: ...\nNEXT: ...\n"
    )


def _numbered_evidence_prompt(case: Any) -> str:
    parts = [case.user_prompt.rstrip(), "", "EVIDENCE BLOCKS:"]
    for i, src in enumerate(case.supporting_sources, start=1):
        parts.append(f"{i}. [{src.citation_key}] {src.title}")
        parts.append(src.content)
        parts.append("")
    parts.append("Cite using citation keys only (e.g. SRC-A).")
    return "\n".join(parts).strip() + "\n"


def _fact_inference_prompt(case: Any) -> str:
    base = build_user_prompt(case)
    return (
        base
        + "\nRespond with sections: FACTS (cited), INFERENCES (labeled), OPEN_QUESTIONS, "
        + "and do not present inferences as facts.\n"
    )


def plan_jobs() -> list[dict[str, Any]]:
    """Bounded plan (~25 generations)."""
    jobs: list[dict[str, Any]] = []
    # A — output caps (skip baseline-identical 512 for long-doc; include higher caps)
    for case_id in (
        "cb-023-long-memo-key-facts",
        "cb-024-long-policy-exceptions",
        "cb-001-evidence-grounded-investigation",
    ):
        for tokens in (1024, 2048):
            jobs.append(
                {
                    "cohort": "A_output_cap",
                    "case_id": case_id,
                    "max_new_tokens": tokens,
                    "enable_thinking": False,
                    "prompt_variant": "original",
                    "rep": 0,
                }
            )
    # B — thinking enabled vs disabled (disabled re-run for 2 controls + enabled for 4)
    for case_id in (
        "cb-019-metric-contradiction",
        "cb-004-hypothesis-ranking-with-gaps",
        "cb-018-schedule-contradiction",
        "cb-015-citation-key-discipline",
    ):
        jobs.append(
            {
                "cohort": "B_thinking",
                "case_id": case_id,
                "max_new_tokens": 512,
                "enable_thinking": True,
                "prompt_variant": "original",
                "rep": 0,
            }
        )
    for case_id in ("cb-019-metric-contradiction", "cb-015-citation-key-discipline"):
        jobs.append(
            {
                "cohort": "B_thinking",
                "case_id": case_id,
                "max_new_tokens": 512,
                "enable_thinking": False,
                "prompt_variant": "original",
                "rep": 0,
            }
        )
    # C — prompt format
    for variant in ("original", "clarified_format", "schema_oriented"):
        jobs.append(
            {
                "cohort": "C_prompt_format",
                "case_id": "cb-027-exact-output-format",
                "max_new_tokens": 512,
                "enable_thinking": False,
                "prompt_variant": variant,
                "rep": 0,
            }
        )
    # D — evidence delimiters
    for case_id in (
        "cb-008-log-vs-witness-grounding",
        "cb-010-email-thread-grounding",
    ):
        for variant in ("numbered_blocks", "fact_inference_instructions"):
            jobs.append(
                {
                    "cohort": "D_evidence_delimiters",
                    "case_id": case_id,
                    "max_new_tokens": 512,
                    "enable_thinking": False,
                    "prompt_variant": variant,
                    "rep": 0,
                }
            )
    # E — stability
    for case_id in (
        "cb-019-metric-contradiction",
        "cb-013-name-invention-resistance",
    ):
        for rep in (0, 1, 2):
            jobs.append(
                {
                    "cohort": "E_stability",
                    "case_id": case_id,
                    "max_new_tokens": 512,
                    "enable_thinking": False,
                    "prompt_variant": "original",
                    "rep": rep,
                }
            )
    return jobs


def _render_user_prompt(case: Any, variant: str) -> str:
    if variant == "original":
        return build_user_prompt(case)
    if variant == "clarified_format":
        return _clarified_format_prompt(case)
    if variant == "schema_oriented":
        return _schema_format_prompt(case)
    if variant == "numbered_blocks":
        return _numbered_evidence_prompt(case)
    if variant == "fact_inference_instructions":
        return _fact_inference_prompt(case)
    raise ValueError(f"unknown prompt variant: {variant}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "model-cards/qwen/qwen3-8b.manifest.json",
    )
    parser.add_argument(
        "--run-id",
        default="20260722T220000Z-2ediag01",
        help="Must match YYYYMMDDTHHMMSSZ-<8 hex>",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    lock_path = ROOT / "evaluations/baselines/qwen3-8b-cobrabench-v0.1.json"
    if args.run_id == BASELINE_RUN:
        raise SystemExit("refusing to reuse official baseline run id")

    jobs = plan_jobs()
    out_root = ROOT / "evaluations" / "results" / "diagnostics" / "qwen3-8b-phase-2e" / args.run_id
    assert_baseline_not_overwritten(lock_path, out_root, repo_root=ROOT)
    out_root.mkdir(parents=True, exist_ok=True)
    cases = {c.case_id: c for c in load_release_cases("0.1")}
    plan_path = out_root / "diagnostic-plan.json"
    _write_json(
        plan_path,
        {
            "run_id": args.run_id,
            "not_official_cobrabench": True,
            "baseline_run_id": BASELINE_RUN,
            "job_count": len(jobs),
            "jobs": jobs,
            "created_at": datetime.now(UTC).isoformat(),
        },
    )
    if args.dry_run:
        print(json.dumps({"dry_run": True, "job_count": len(jobs), "out": str(out_root)}))
        return 0

    manifest = ModelManifest.model_validate_json(args.manifest.read_text(encoding="utf-8"))
    adapter = QwenLocalAdapter(
        load_in_4bit=True,
        max_memory={0: "9GiB", "cpu": "18GiB"},
    )
    engine = LocalInferenceEngine(adapter)
    results: list[dict[str, Any]] = []
    try:
        for idx, job in enumerate(jobs):
            case = cases[job["case_id"]]
            user_prompt = _render_user_prompt(case, job["prompt_variant"])
            req = InferenceRequest(
                system_prompt=case.system_prompt,
                user_prompt=user_prompt,
                temperature=0.0,
                seed=123,
                max_new_tokens=int(job["max_new_tokens"]),
                enable_thinking=bool(job["enable_thinking"]),
            )
            job_id = (
                f"{job['cohort']}__{job['case_id']}__t{job['max_new_tokens']}"
                f"__think{int(job['enable_thinking'])}"
                f"__{job['prompt_variant']}__r{job['rep']}"
            )
            print(f"[{idx + 1}/{len(jobs)}] {job_id}", flush=True)
            try:
                result = engine.run(
                    manifest=manifest,
                    manifest_ref=str(args.manifest),
                    request=req,
                    persist=False,
                )
                resp_dir = out_root / "responses"
                resp_dir.mkdir(exist_ok=True)
                (resp_dir / f"{job_id}.txt").write_text(result.assistant_response, encoding="utf-8")
                meta = {
                    **job,
                    "job_id": job_id,
                    "status": "ok",
                    "input_token_count": result.input_token_count,
                    "output_token_count": result.output_token_count,
                    "total_latency_ms": result.total_latency_ms,
                    "tokens_per_second": result.tokens_per_second,
                    "finish_reason": result.finish_reason,
                    "warnings": result.warnings,
                    "response_excerpt": result.assistant_response[:500],
                }
                _write_json(resp_dir / f"{job_id}.meta.json", meta)
                results.append(meta)
            except Exception as exc:  # noqa: BLE001
                err = {
                    **job,
                    "job_id": job_id,
                    "status": "error",
                    "error": str(exc),
                }
                results.append(err)
                _write_json(out_root / "errors" / f"{job_id}.json", err)
    finally:
        adapter.unload()

    summary = {
        "run_id": args.run_id,
        "not_official_cobrabench": True,
        "baseline_run_id": BASELINE_RUN,
        "completed_at": datetime.now(UTC).isoformat(),
        "job_count": len(jobs),
        "ok": sum(1 for r in results if r.get("status") == "ok"),
        "errors": sum(1 for r in results if r.get("status") == "error"),
        "results": results,
    }
    _write_json(out_root / "diagnostic-summary.json", summary)
    print(json.dumps({"out": str(out_root), "ok": summary["ok"], "errors": summary["errors"]}))
    return 0 if summary["errors"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
