"""Benchmark engine — score, compare, report (no routing changes)."""

from __future__ import annotations

import hashlib
import json
import statistics
import uuid
from typing import Any

from cobra_core.benchmark.audit import BENCHMARK_AUDIT
from cobra_core.benchmark.config import BenchmarkConfig, load_benchmark_config
from cobra_core.benchmark.metrics import BENCHMARK_METRICS
from cobra_core.benchmark.registry import DATASET_REGISTRY, DatasetRegistry
from cobra_core.benchmark.scoring import build_calibration_curve, score_case
from cobra_core.benchmark.schemas import (
    BenchmarkDataset,
    BenchmarkExecution,
    BenchmarkRunResult,
    CaseScore,
    RepeatabilityResult,
)


def _output_fingerprint(output: dict[str, Any]) -> str:
    payload = json.dumps(output, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _recommendations(scores: list[CaseScore], curve: tuple) -> tuple[str, ...]:
    tips: list[str] = []
    if not scores:
        return ("No cases scored.",)
    avg_cite = statistics.mean(s.citation_accuracy for s in scores)
    avg_find = statistics.mean(s.finding_accuracy for s in scores)
    avg_calib = statistics.mean(s.confidence_calibration for s in scores)
    if avg_cite < 0.7:
        tips.append("Improve citation grounding; unsupported or missing citations detected.")
    if avg_find < 0.7:
        tips.append("Finding accuracy below threshold; review gold alignment and hallucinations.")
    if avg_calib < 0.6:
        tips.append("Confidence calibration weak; high-confidence incorrect answers present.")
    high = next((b for b in curve if b.label == "high"), None)
    if high and high.count and high.accuracy < 0.8:
        tips.append("High-confidence bin accuracy is low — tighten confidence policy.")
    if not tips:
        tips.append("Scores within thresholds for this run; continue regression monitoring.")
    return tuple(tips)


class BenchmarkEngine:
    """
    Truth engine for Investigation Skills.

    Accepts isolated executions (does not enqueue approvals or alter AIR routing).
    """

    def __init__(
        self,
        *,
        config: BenchmarkConfig | None = None,
        registry: DatasetRegistry | None = None,
    ) -> None:
        self.config = config or load_benchmark_config()
        self.registry = registry if registry is not None else DATASET_REGISTRY

    def score_executions(
        self,
        dataset: BenchmarkDataset,
        executions: list[BenchmarkExecution],
        *,
        provider_id: str = "mock",
        workflow_id: str = "isf_default",
        run_id: str | None = None,
        repeatability: tuple[RepeatabilityResult, ...] = (),
    ) -> BenchmarkRunResult:
        if not self.config.enabled:
            raise RuntimeError("benchmark framework disabled")
        if not self.config.isolate_from_production:
            raise RuntimeError("benchmark must remain isolated from production")

        by_case = {e.case_id: e for e in executions}
        scores: list[CaseScore] = []
        for case in dataset.cases:
            ex = by_case.get(case.case_id)
            if ex is None:
                ex = BenchmarkExecution(
                    case_id=case.case_id,
                    skill_id=case.skill_id,
                    provider_id=provider_id,
                    workflow_id=workflow_id,
                    output={},
                    status="missing_execution",
                    error_code="missing_execution",
                )
            scores.append(score_case(case, ex, self.config))

        overall = round(statistics.mean(s.overall for s in scores), 4) if scores else 0.0
        lat_avg = (
            round(statistics.mean(s.latency_ms for s in scores), 2) if scores else 0.0
        )
        cost = round(sum(s.estimated_cost_usd for s in scores), 6)
        curve = build_calibration_curve(scores, executions)
        # Pass when overall clears threshold and no non-missing-evidence case hard-fails.
        hard_fails = [
            s
            for s in scores
            if (not s.passed) and not case_expect_missing(dataset, s.case_id)
        ]
        passed = overall >= self.config.pass_threshold and not hard_fails

        rid = run_id or f"brun_{uuid.uuid4().hex[:12]}"
        recs = _recommendations(scores, curve)
        result = BenchmarkRunResult(
            run_id=rid,
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            provider_id=provider_id,
            workflow_id=workflow_id,
            case_scores=tuple(scores),
            overall_score=overall,
            passed=passed,
            latency_avg_ms=lat_avg,
            cost_total_usd=cost,
            calibration_curve=curve,
            repeatability=repeatability,
            recommendations=recs,
        )
        rep_rate = None
        if repeatability:
            rep_rate = statistics.mean(r.identical_output_rate for r in repeatability)
        BENCHMARK_METRICS.record_run(
            passed=passed,
            overall_score=overall,
            latency_avg_ms=lat_avg,
            cost_total_usd=cost,
            repeatability_rate=rep_rate,
        )
        BENCHMARK_AUDIT.record(
            "benchmark_run",
            run_id=rid,
            dataset_id=dataset.dataset_id,
            dataset_version=dataset.version,
            provider_id=provider_id,
            workflow_id=workflow_id,
            overall_score=overall,
            passed=passed,
            case_count=len(scores),
        )
        return result

    def measure_repeatability(
        self,
        case_id: str,
        executions: list[BenchmarkExecution],
    ) -> RepeatabilityResult:
        if not executions:
            return RepeatabilityResult(case_id, 0, 0.0, 0.0, 0.0, 0.0)
        fps = [_output_fingerprint(e.output if isinstance(e.output, dict) else {}) for e in executions]
        identical = sum(1 for f in fps if f == fps[0]) / len(fps)
        # Score each against a temporary case stub via overall fields if present.
        confs = [float((e.output or {}).get("confidence") or 0.0) for e in executions]
        cites = [
            tuple(sorted(str(x) for x in ((e.output or {}).get("citations") or [])))
            for e in executions
        ]
        cite_fps = [hashlib.sha256(repr(c).encode()).hexdigest() for c in cites]
        cite_ident = sum(1 for f in cite_fps if f == cite_fps[0]) / len(cite_fps)
        score_proxy = [float((e.metadata or {}).get("score_overall") or 0.0) for e in executions]
        if all(s == 0.0 for s in score_proxy):
            score_var = 0.0
        else:
            score_var = round(statistics.pvariance(score_proxy), 6) if len(score_proxy) > 1 else 0.0
        conf_var = round(statistics.pvariance(confs), 6) if len(confs) > 1 else 0.0
        return RepeatabilityResult(
            case_id=case_id,
            runs=len(executions),
            identical_output_rate=round(identical, 4),
            score_variance=score_var,
            confidence_variance=conf_var,
            citation_variance=round(1.0 - cite_ident, 4),
        )

    def compare_providers(
        self,
        dataset: BenchmarkDataset,
        by_provider: dict[str, list[BenchmarkExecution]],
        *,
        workflow_id: str = "isf_default",
    ) -> dict[str, BenchmarkRunResult]:
        """Score the same dataset across providers. Does not change routing."""
        out: dict[str, BenchmarkRunResult] = {}
        for provider_id, executions in sorted(by_provider.items()):
            out[provider_id] = self.score_executions(
                dataset,
                executions,
                provider_id=provider_id,
                workflow_id=workflow_id,
            )
        BENCHMARK_AUDIT.record(
            "provider_comparison",
            dataset_id=dataset.dataset_id,
            providers=list(out.keys()),
            scores={k: v.overall_score for k, v in out.items()},
        )
        return out


def case_expect_missing(dataset: BenchmarkDataset, case_id: str) -> bool:
    for case in dataset.cases:
        if case.case_id == case_id:
            return case.gold.expect_missing_evidence
    return False
