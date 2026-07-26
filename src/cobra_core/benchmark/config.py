"""Benchmark framework configuration (measurement only)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _float(raw: str | None, default: float) -> float:
    if raw is None or not str(raw).strip():
        return default
    return float(raw)


@dataclass(frozen=True)
class BenchmarkConfig:
    """Runtime knobs for the benchmark package."""

    enabled: bool = True
    # Isolation: never write ISF/KEF/CIAL production audit or approval queues.
    isolate_from_production: bool = True
    pass_threshold: float = 0.70
    repeat_default: int = 3
    # Scoring weights (must sum ~1.0; normalized at use).
    weight_finding_accuracy: float = 0.30
    weight_citation_accuracy: float = 0.25
    weight_schema_validity: float = 0.15
    weight_completeness: float = 0.15
    weight_confidence_calibration: float = 0.15
    # Cost estimate ($ per 1k tokens) for reporting only — not billing.
    cost_per_1k_input_tokens: float = 0.0
    cost_per_1k_output_tokens: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.pass_threshold <= 1.0:
            raise ValueError("pass_threshold must be in [0, 1]")
        if self.repeat_default < 1:
            raise ValueError("repeat_default must be >= 1")


def load_benchmark_config(env: dict[str, str] | None = None) -> BenchmarkConfig:
    e = env if env is not None else os.environ
    return BenchmarkConfig(
        enabled=_bool(e.get("BENCHMARK_ENABLED"), True),
        isolate_from_production=_bool(e.get("BENCHMARK_ISOLATE"), True),
        pass_threshold=_float(e.get("BENCHMARK_PASS_THRESHOLD"), 0.70),
        repeat_default=max(1, int(e.get("BENCHMARK_REPEAT_DEFAULT") or "3")),
        weight_finding_accuracy=_float(e.get("BENCHMARK_W_FINDING"), 0.30),
        weight_citation_accuracy=_float(e.get("BENCHMARK_W_CITATION"), 0.25),
        weight_schema_validity=_float(e.get("BENCHMARK_W_SCHEMA"), 0.15),
        weight_completeness=_float(e.get("BENCHMARK_W_COMPLETENESS"), 0.15),
        weight_confidence_calibration=_float(e.get("BENCHMARK_W_CALIBRATION"), 0.15),
        cost_per_1k_input_tokens=_float(e.get("BENCHMARK_COST_IN_1K"), 0.0),
        cost_per_1k_output_tokens=_float(e.get("BENCHMARK_COST_OUT_1K"), 0.0),
    )
