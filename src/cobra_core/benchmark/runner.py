"""Benchmark runner — executes cases via an injected callable (no routing changes)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

from cobra_core.benchmark.config import BenchmarkConfig, load_benchmark_config
from cobra_core.benchmark.engine import BenchmarkEngine
from cobra_core.benchmark.registry import DATASET_REGISTRY, DatasetRegistry
from cobra_core.benchmark.schemas import (
    BenchmarkCase,
    BenchmarkDataset,
    BenchmarkExecution,
    BenchmarkRunResult,
    ExpectedEvidence,
)
from cobra_core.isf.schemas import empty_skill_output

# Executor signature: returns skill output dict and optional meta.
ExecutorFn = Callable[[BenchmarkCase, str], dict[str, Any]]


def mock_executor(case: BenchmarkCase, provider_id: str) -> dict[str, Any]:
    """
    Deterministic mock executor aligned to gold for regression baselines.

    Does not call AIR/CIAL/providers. Used for framework self-tests and offline runs.
    """
    _ = provider_id
    gold = case.gold
    if gold.expect_missing_evidence:
        return {
            "status": "error",
            "error": {"code": "missing_required_evidence"},
            "output": empty_skill_output(
                case.skill_id,
                summary="Missing required evidence",
                confidence=0.0,
                missing_information=list(gold.missing_information) or ["required evidence missing"],
                citations=[],
            ),
        }
    base = empty_skill_output(
        case.skill_id,
        summary=" ".join(gold.summary_contains) or f"Mock result for {case.case_id}",
        confidence=min(0.5, gold.confidence_max),
        citations=list(gold.citations),
        missing_information=list(gold.missing_information),
    )
    for key, value in gold.structured_fields.items():
        if key in base:
            base[key] = value
    if "findings" in base and gold.findings:
        base["findings"] = list(gold.findings)
    if "damage_locations" in base and gold.findings:
        base["damage_locations"] = list(gold.findings)
    if "anomalies" in base and gold.findings:
        base["anomalies"] = list(gold.findings)
    if "themes" in base and gold.findings:
        base["themes"] = list(gold.findings)
    # Contract analysis has no "findings" field — map gold findings onto risks.
    if "risks" in base and gold.findings and not base.get("risks"):
        base["risks"] = list(gold.findings)
    elif "risks" in base and gold.findings:
        # Prefer full gold finding set for scoring when structured risks are a subset.
        structured_risks = gold.structured_fields.get("risks")
        if isinstance(structured_risks, list) and len(structured_risks) < len(gold.findings):
            base["risks"] = list(gold.findings)
    if "differences" in base:
        base["differences"] = list(
            gold.structured_fields.get("differences") or list(gold.findings[:1])
        )
    if "agreements" in base and "agreements" in gold.structured_fields:
        base["agreements"] = list(gold.structured_fields["agreements"])
    if "events" in base and gold.findings:
        base["events"] = [{"label": f} for f in gold.findings]
    return {"status": "pending_approval", "output": base, "error": {}}


class BenchmarkRunner:
    """
    Runs a dataset through an executor and scores results.

    Provider id is a label for comparison only — never mutates AIR routing.
    """

    def __init__(
        self,
        *,
        config: BenchmarkConfig | None = None,
        registry: DatasetRegistry | None = None,
        engine: BenchmarkEngine | None = None,
        executor: ExecutorFn | None = None,
    ) -> None:
        self.config = config or load_benchmark_config()
        self.registry = registry if registry is not None else DATASET_REGISTRY
        self.engine = engine or BenchmarkEngine(config=self.config, registry=self.registry)
        self.executor = executor or mock_executor

    def run_dataset(
        self,
        dataset_id: str,
        *,
        version: str | None = None,
        provider_id: str = "mock",
        workflow_id: str = "isf_default",
        repeats: int = 1,
    ) -> BenchmarkRunResult:
        dataset = self.registry.get(dataset_id, version)
        return self.run(dataset, provider_id=provider_id, workflow_id=workflow_id, repeats=repeats)

    def run(
        self,
        dataset: BenchmarkDataset,
        *,
        provider_id: str = "mock",
        workflow_id: str = "isf_default",
        repeats: int = 1,
    ) -> BenchmarkRunResult:
        repeats = max(1, repeats)
        primary: list[BenchmarkExecution] = []
        rep_results = []
        for case in dataset.cases:
            run_bucket: list[BenchmarkExecution] = []
            for _ in range(repeats):
                t0 = time.perf_counter()
                raw = self.executor(case, provider_id)
                ms = (time.perf_counter() - t0) * 1000
                run_bucket.append(
                    _to_execution(case, provider_id, workflow_id, raw, ms, self.config)
                )
            primary.append(run_bucket[0])
            if repeats > 1:
                scored = self.engine.score_executions(
                    _single_case_dataset(dataset, case),
                    [run_bucket[0]],
                    provider_id=provider_id,
                    workflow_id=workflow_id,
                )
                for ex in run_bucket:
                    ex.metadata["score_overall"] = scored.overall_score
                rep_results.append(self.engine.measure_repeatability(case.case_id, run_bucket))

        return self.engine.score_executions(
            dataset,
            primary,
            provider_id=provider_id,
            workflow_id=workflow_id,
            repeatability=tuple(rep_results),
        )

    def compare_providers(
        self,
        dataset_id: str,
        provider_ids: list[str],
        *,
        version: str | None = None,
        workflow_id: str = "isf_default",
    ) -> dict[str, BenchmarkRunResult]:
        dataset = self.registry.get(dataset_id, version)
        by_provider: dict[str, list[BenchmarkExecution]] = {}
        for pid in provider_ids:
            executions: list[BenchmarkExecution] = []
            for case in dataset.cases:
                t0 = time.perf_counter()
                raw = self.executor(case, pid)
                ms = (time.perf_counter() - t0) * 1000
                executions.append(_to_execution(case, pid, workflow_id, raw, ms, self.config))
            by_provider[pid] = executions
        return self.engine.compare_providers(dataset, by_provider, workflow_id=workflow_id)


def _to_execution(
    case: BenchmarkCase,
    provider_id: str,
    workflow_id: str,
    raw: dict[str, Any],
    latency_ms: float,
    config: BenchmarkConfig,
) -> BenchmarkExecution:
    output = raw.get("output") if isinstance(raw.get("output"), dict) else raw
    if not isinstance(output, dict):
        output = {}
    raw_error = raw.get("error")
    err: dict[str, Any] = raw_error if isinstance(raw_error, dict) else {}
    return BenchmarkExecution(
        case_id=case.case_id,
        skill_id=case.skill_id,
        provider_id=provider_id,
        workflow_id=workflow_id,
        output=output,
        latency_ms=latency_ms,
        status=str(raw.get("status") or "completed"),
        error_code=str(err.get("code") or ""),
        estimated_cost_usd=_estimate_cost(config, raw),
        metadata={"evidence": _evidence_meta(case.evidence)},
    )


def _estimate_cost(config: BenchmarkConfig, raw: dict[str, Any]) -> float:
    raw_usage = raw.get("usage")
    meta: dict[str, Any] = raw_usage if isinstance(raw_usage, dict) else {}
    inn = int(meta.get("input_tokens") or 0)
    out = int(meta.get("output_tokens") or 0)
    return round(
        (inn / 1000.0) * config.cost_per_1k_input_tokens
        + (out / 1000.0) * config.cost_per_1k_output_tokens,
        6,
    )


def _evidence_meta(evidence: tuple[ExpectedEvidence, ...]) -> list[dict[str, str]]:
    return [{"evidence_type": e.evidence_type, "ref_id": e.ref_id} for e in evidence]


def _single_case_dataset(dataset: BenchmarkDataset, case: BenchmarkCase) -> BenchmarkDataset:
    return BenchmarkDataset(
        dataset_id=dataset.dataset_id,
        version=dataset.version,
        skill_id=dataset.skill_id,
        title=dataset.title,
        cases=(case,),
        description=dataset.description,
    )
