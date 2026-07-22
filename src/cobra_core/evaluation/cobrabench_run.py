"""CobraBench evaluation runner (dry-run safe for tests)."""

from __future__ import annotations

import json
import platform
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cobra_core.benchmarks.release import load_release_cases, release_dir
from cobra_core.evaluation.citations import citation_metrics
from cobra_core.evaluation.contradiction import contradiction_metrics
from cobra_core.evaluation.hallucination import classify_hallucination_severity
from cobra_core.evaluation.refusal import refusal_metrics
from cobra_core.evaluation.rule_checks import (
    run_objective_checks,
    run_rule_based_behavior_checks,
    score_from_checks,
)
from cobra_core.schemas.benchmark import BenchmarkCase
from cobra_core.schemas.inference import InferenceRequest
from cobra_core.schemas.manifest import ModelManifest

EVALUATOR_VERSION = "cobrabench-evaluator-v0.1.0"
RUN_ID_PATTERN = re.compile(r"^\d{8}T\d{6}Z-[a-f0-9]{8}$")

REQUIRED_RUN_ARTIFACTS = (
    "run.json",
    "environment.json",
    "model-reference.json",
    "benchmark-reference.json",
    "objective-metrics.json",
    "rule-checks.json",
    "human-scores.json",
    "judge-scores.json",
    "errors.json",
)
REQUIRED_RUN_DIRS = ("prompts", "responses")

_PENDING_REVIEW = {"status": "pending", "scores": []}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _results_root(benchmark_version: str, model_slug: str) -> Path:
    # Keep dotted version in the path: cobrabench-v0.1/...
    return (
        _repo_root() / "evaluations" / "results" / f"cobrabench-v{benchmark_version}" / model_slug
    )


def generate_run_id(*, at: datetime | None = None) -> str:
    """Return a reproducible-format run id: ``YYYYMMDDTHHMMSSZ-<8 hex>``."""
    moment = at or datetime.now(UTC)
    stamp = moment.strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    run_id = f"{stamp}-{suffix}"
    if not RUN_ID_PATTERN.match(run_id):
        raise ValueError(f"generated run_id failed pattern check: {run_id}")
    return run_id


def validate_score_in_range(score: float, *, field_name: str = "score") -> None:
    """Raise ValueError when score is outside [0, 1]."""
    if score < 0.0 or score > 1.0:
        raise ValueError(f"{field_name} must be in [0, 1], got {score}")


def detect_missing_human_review(human_scores: dict[str, Any]) -> bool:
    """Return True when human review is still pending or empty."""
    status = str(human_scores.get("status", "pending")).lower()
    scores = human_scores.get("scores", [])
    return status == "pending" or not scores


def build_user_prompt(case: BenchmarkCase) -> str:
    """Append supporting sources clearly labeled with citation keys."""
    parts = [case.user_prompt.rstrip()]
    if case.supporting_sources:
        parts.append("")
        parts.append("Supporting sources (cite using the citation keys):")
        for source in case.supporting_sources:
            parts.append("")
            parts.append(f"[{source.citation_key}] {source.title}")
            parts.append(source.content)
    return "\n".join(parts).strip() + "\n"


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def _allowed_keys(case: BenchmarkCase) -> list[str]:
    if case.citation_requirements is not None:
        return list(case.citation_requirements.allowed_keys)
    return [src.citation_key for src in case.supporting_sources]


def _source_texts(case: BenchmarkCase) -> dict[str, str]:
    return {src.citation_key: src.content for src in case.supporting_sources}


def _compute_case_metrics(case: BenchmarkCase, response: str) -> dict[str, Any]:
    allowed = _allowed_keys(case)
    sources = _source_texts(case)
    objective = run_objective_checks(case, response)
    behavior = run_rule_based_behavior_checks(case, response)
    return {
        "citation_metrics": citation_metrics(response, allowed, sources or None),
        "hallucination": classify_hallucination_severity(response, case),
        "contradiction_metrics": contradiction_metrics(response, case),
        "refusal_metrics": refusal_metrics(response, case),
        "objective_checks": objective,
        "behavior_checks": behavior,
        "objective_score": score_from_checks(objective),
        "behavior_score": score_from_checks(behavior),
    }


def _write_prompt_artifacts(run_dir: Path, case: BenchmarkCase) -> None:
    user_prompt = build_user_prompt(case)
    prompt_payload = {
        "case_id": case.case_id,
        "system_prompt": case.system_prompt,
        "user_prompt": user_prompt,
    }
    _write_json(run_dir / "prompts" / f"{case.case_id}.json", prompt_payload)


def _initialize_run_directory(
    run_dir: Path,
    *,
    manifest_path: Path,
    manifest: ModelManifest | None,
    benchmark_version: str,
    model_slug: str,
    run_id: str,
    dry_run: bool,
    inference_settings: dict[str, Any],
    environment_reference: str | None,
) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "prompts").mkdir(exist_ok=True)
    (run_dir / "responses").mkdir(exist_ok=True)

    started_at = datetime.now(UTC).isoformat()
    _write_json(
        run_dir / "run.json",
        {
            "run_id": run_id,
            "benchmark_version": benchmark_version,
            "model_slug": model_slug,
            "manifest_path": str(manifest_path),
            "evaluator_version": EVALUATOR_VERSION,
            "dry_run": dry_run,
            "started_at": started_at,
            "inference_settings": inference_settings,
            "cases": [],
        },
    )
    _write_json(
        run_dir / "environment.json",
        {
            "environment_reference": environment_reference,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
        },
    )
    _write_json(
        run_dir / "model-reference.json",
        {
            "manifest_path": str(manifest_path),
            "model_name": manifest.model_name if manifest else None,
            "model_revision": manifest.model_revision if manifest else None,
            "provider": manifest.provider if manifest else None,
        },
    )
    _write_json(
        run_dir / "benchmark-reference.json",
        {
            "benchmark_version": benchmark_version,
            "release_dir": str(release_dir(benchmark_version)),
            "evaluator_version": EVALUATOR_VERSION,
        },
    )
    _write_json(run_dir / "human-scores.json", dict(_PENDING_REVIEW))
    _write_json(run_dir / "judge-scores.json", dict(_PENDING_REVIEW))
    _write_json(run_dir / "errors.json", {"errors": []})
    _write_json(
        run_dir / "objective-metrics.json", {"evaluator_version": EVALUATOR_VERSION, "cases": {}}
    )
    _write_json(run_dir / "rule-checks.json", {"evaluator_version": EVALUATOR_VERSION, "cases": {}})


def _append_error(run_dir: Path, error_entry: dict[str, Any]) -> None:
    path = run_dir / "errors.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.setdefault("errors", []).append(error_entry)
    _write_json(path, payload)


def _finalize_run(run_dir: Path, case_summaries: list[dict[str, Any]]) -> None:
    run_path = run_dir / "run.json"
    payload = json.loads(run_path.read_text(encoding="utf-8"))
    payload["cases"] = case_summaries
    payload["completed_at"] = datetime.now(UTC).isoformat()
    payload["case_count"] = len(case_summaries)
    _write_json(run_path, payload)


def run_cobrabench(
    *,
    manifest_path: Path,
    model_slug: str,
    benchmark_version: str = "0.1",
    run_id: str | None = None,
    max_new_tokens: int = 512,
    temperature: float = 0.0,
    seed: int = 123,
    enable_thinking: bool = False,
    case_ids: list[str] | None = None,
    dry_run: bool = False,
) -> Path:
    """
    Run CobraBench for a model manifest.

    When ``dry_run=True``, only prompts and run scaffolding are written (no model load).
    """
    manifest_path = manifest_path.resolve()
    resolved_run_id = run_id or generate_run_id()
    if not RUN_ID_PATTERN.match(resolved_run_id):
        raise ValueError(f"run_id must match {RUN_ID_PATTERN.pattern}, got {resolved_run_id!r}")

    manifest: ModelManifest | None = None
    if not dry_run:
        manifest = ModelManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))

    inference_settings = {
        "temperature": temperature,
        "max_new_tokens": max_new_tokens,
        "seed": seed,
        "enable_thinking": enable_thinking,
    }
    env_ref_path = _repo_root() / "evaluations" / "environment" / "local-machine.json"
    environment_reference = str(env_ref_path) if env_ref_path.exists() else None

    run_dir = _results_root(benchmark_version, model_slug) / resolved_run_id
    _initialize_run_directory(
        run_dir,
        manifest_path=manifest_path,
        manifest=manifest,
        benchmark_version=benchmark_version,
        model_slug=model_slug,
        run_id=resolved_run_id,
        dry_run=dry_run,
        inference_settings=inference_settings,
        environment_reference=environment_reference,
    )

    all_cases = load_release_cases(benchmark_version)
    if case_ids:
        selected = {case_id: None for case_id in case_ids}
        cases = [case for case in all_cases if case.case_id in selected]
        missing = set(case_ids) - {case.case_id for case in cases}
        if missing:
            raise ValueError(f"Unknown case_ids: {sorted(missing)}")
    else:
        cases = all_cases

    objective_doc: dict[str, Any] = {
        "evaluator_version": EVALUATOR_VERSION,
        "cases": {},
    }
    rule_doc: dict[str, Any] = {
        "evaluator_version": EVALUATOR_VERSION,
        "cases": {},
    }
    case_summaries: list[dict[str, Any]] = []

    adapter = None
    engine = None
    if not dry_run:
        from cobra_core.inference.engine import LocalInferenceEngine
        from cobra_core.providers.qwen_local import QwenLocalAdapter

        adapter = QwenLocalAdapter(
            load_in_4bit=True,
            max_memory={0: "9GiB", "cpu": "18GiB"},
        )
        engine = LocalInferenceEngine(adapter)
        assert manifest is not None

    try:
        for case in cases:
            _write_prompt_artifacts(run_dir, case)
            summary: dict[str, Any] = {"case_id": case.case_id, "status": "pending"}

            if dry_run:
                summary["status"] = "prompt_only"
                case_summaries.append(summary)
                continue

            assert engine is not None and manifest is not None
            user_prompt = build_user_prompt(case)
            request = InferenceRequest(
                system_prompt=case.system_prompt,
                user_prompt=user_prompt,
                temperature=temperature,
                max_new_tokens=max_new_tokens,
                seed=seed,
                enable_thinking=enable_thinking,
            )
            try:
                result = engine.run(
                    manifest=manifest,
                    manifest_ref=str(manifest_path),
                    request=request,
                    environment_reference=environment_reference,
                    results_dir=None,
                    persist=False,
                )
                response_text = result.assistant_response
                response_path = run_dir / "responses" / f"{case.case_id}.txt"
                response_path.write_text(response_text, encoding="utf-8")

                metrics = _compute_case_metrics(case, response_text)
                objective_doc["cases"][case.case_id] = {
                    "citation_metrics": metrics["citation_metrics"],
                    "hallucination": metrics["hallucination"],
                    "contradiction_metrics": metrics["contradiction_metrics"],
                    "refusal_metrics": metrics["refusal_metrics"],
                    "objective_score": metrics["objective_score"],
                }
                rule_doc["cases"][case.case_id] = {
                    "objective_checks": metrics["objective_checks"],
                    "behavior_checks": metrics["behavior_checks"],
                    "objective_score": metrics["objective_score"],
                    "behavior_score": metrics["behavior_score"],
                }
                summary.update(
                    {
                        "status": "ok",
                        "response_path": str(response_path.relative_to(run_dir)),
                        "objective_score": metrics["objective_score"],
                        "behavior_score": metrics["behavior_score"],
                        "latency_ms": result.total_latency_ms,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — accumulate and continue
                summary["status"] = "error"
                summary["error"] = str(exc)
                _append_error(
                    run_dir,
                    {
                        "case_id": case.case_id,
                        "error": str(exc),
                        "timestamp": datetime.now(UTC).isoformat(),
                    },
                )
            case_summaries.append(summary)
    finally:
        if adapter is not None:
            adapter.unload()

    _write_json(run_dir / "objective-metrics.json", objective_doc)
    _write_json(run_dir / "rule-checks.json", rule_doc)
    _finalize_run(run_dir, case_summaries)
    return run_dir
