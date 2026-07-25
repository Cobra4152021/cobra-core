"""AIR observability counters (in-process; safe aggregates only)."""

from __future__ import annotations

import threading
from collections import Counter
from typing import Any

from cobra_core.air.types import AirDecision, CostClass, LatencyClass


class AirMetrics:
    """Thread-safe routing metrics for AIR."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.routing_count = 0
        self.routing_failures = 0
        self.health_failures = 0
        self.provider_selections: Counter[str] = Counter()
        self.model_selections: Counter[str] = Counter()
        self.cost_class_distribution: Counter[str] = Counter()
        self.latency_class_distribution: Counter[str] = Counter()
        self.failure_codes: Counter[str] = Counter()

    def record_decision(self, decision: AirDecision) -> None:
        with self._lock:
            self.routing_count += 1
            self.provider_selections[decision.provider_id] += 1
            self.model_selections[f"{decision.provider_id}/{decision.model_id}"] += 1
            self.cost_class_distribution[decision.estimated_cost_class.value] += 1
            self.latency_class_distribution[decision.latency_class.value] += 1

    def record_failure(self, *, air_code: str, health_related: bool = False) -> None:
        with self._lock:
            self.routing_count += 1
            self.routing_failures += 1
            self.failure_codes[air_code] += 1
            if health_related:
                self.health_failures += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "routing_count": self.routing_count,
                "routing_failures": self.routing_failures,
                "health_failures": self.health_failures,
                "provider_selections": dict(self.provider_selections),
                "model_selections": dict(self.model_selections),
                "cost_class_distribution": dict(self.cost_class_distribution),
                "latency_class_distribution": dict(self.latency_class_distribution),
                "failure_codes": dict(self.failure_codes),
            }

    def reset(self) -> None:
        with self._lock:
            self.routing_count = 0
            self.routing_failures = 0
            self.health_failures = 0
            self.provider_selections.clear()
            self.model_selections.clear()
            self.cost_class_distribution.clear()
            self.latency_class_distribution.clear()
            self.failure_codes.clear()


def cost_class_value(value: CostClass | str) -> str:
    return value.value if isinstance(value, CostClass) else str(value)


def latency_class_value(value: LatencyClass | str) -> str:
    return value.value if isinstance(value, LatencyClass) else str(value)
