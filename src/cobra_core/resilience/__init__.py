"""
Reliability & Resilience Framework (RRF) — KC-026.

Executes AIR-selected routes with bounded retries, circuit breakers,
constrained fallback, budget protection, and idempotency.
"""

from __future__ import annotations

from cobra_core.resilience.config import ResilienceConfig, load_resilience_config, rrf_enabled
from cobra_core.resilience.errors import FailureCategory, ResilienceError, traits_for
from cobra_core.resilience.types import (
    CircuitState,
    ExecutionStatus,
    ResilienceRequest,
    ResilienceResult,
    RouteTarget,
)

__all__ = [
    "CircuitState",
    "ExecutionStatus",
    "FailureCategory",
    "ResilienceConfig",
    "ResilienceError",
    "ResilienceRequest",
    "ResilienceResult",
    "RouteTarget",
    "load_resilience_config",
    "rrf_enabled",
    "traits_for",
]


def __getattr__(name: str):
    # Lazy exports to avoid import cycles with ISF.
    if name == "ResilienceExecutor":
        from cobra_core.resilience.executor import ResilienceExecutor

        return ResilienceExecutor
    if name == "RRF_AUDIT":
        from cobra_core.resilience.audit import RRF_AUDIT

        return RRF_AUDIT
    if name == "RRF_METRICS":
        from cobra_core.resilience.metrics import RRF_METRICS

        return RRF_METRICS
    raise AttributeError(name)
