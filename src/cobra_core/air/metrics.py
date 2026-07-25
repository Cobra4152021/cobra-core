"""AIR observability counters (in-process; safe aggregates only)."""

from __future__ import annotations

import threading
import time
from collections import Counter
from typing import Any

from cobra_core.air.types import AirDecision, CostClass, LatencyClass

# Bounded label allow-lists (never prompt/user/evidence/request ids).
_ALLOWED_PROVIDERS = frozenset({"mock", "openai", "unknown"})
_ALLOWED_MODELS = frozenset(
    {
        "cobra-core-qwen3-8b",
        "gpt-5.4-mini",
        "gpt-4o-mini",
        "gpt-test",
        "gpt-x",
        "gpt-live",
        "other",
    }
)


def _bound_provider(provider_id: str) -> str:
    key = (provider_id or "unknown").strip().lower()
    return key if key in _ALLOWED_PROVIDERS else "unknown"


def _bound_model(model_id: str) -> str:
    key = (model_id or "other").strip()
    return key if key in _ALLOWED_MODELS else "other"


class AirMetrics:
    """Thread-safe routing metrics for AIR (Prometheus-ready)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.routing_count = 0
        self.routing_success = 0
        self.routing_failures = 0
        self.health_failures = 0
        self.no_capability_match = 0
        self.policy_exclusion = 0
        self.fail_closed = 0
        self.provider_selections: Counter[str] = Counter()
        self.model_selections: Counter[str] = Counter()
        self.cost_class_distribution: Counter[str] = Counter()
        self.latency_class_distribution: Counter[str] = Counter()
        self.failure_codes: Counter[str] = Counter()
        self.routing_latency_ms_sum = 0
        self.routing_latency_ms_count = 0

    def record_decision(self, decision: AirDecision, *, latency_ms: int = 0) -> None:
        with self._lock:
            self.routing_count += 1
            self.routing_success += 1
            self.provider_selections[_bound_provider(decision.provider_id)] += 1
            self.model_selections[_bound_model(decision.model_id)] += 1
            self.cost_class_distribution[decision.estimated_cost_class.value] += 1
            self.latency_class_distribution[decision.latency_class.value] += 1
            self._observe_latency_unlocked(latency_ms)

    def record_failure(
        self,
        *,
        air_code: str,
        health_related: bool = False,
        latency_ms: int = 0,
    ) -> None:
        with self._lock:
            self.routing_count += 1
            self.routing_failures += 1
            self.fail_closed += 1
            self.failure_codes[air_code] += 1
            if health_related or air_code == "no_healthy_candidate":
                self.health_failures += 1
            if air_code == "no_capability_match":
                self.no_capability_match += 1
            if air_code == "policy_excluded":
                self.policy_exclusion += 1
            self._observe_latency_unlocked(latency_ms)

    def _observe_latency_unlocked(self, latency_ms: int) -> None:
        ms = max(0, int(latency_ms))
        self.routing_latency_ms_sum += ms
        self.routing_latency_ms_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = (
                self.routing_latency_ms_sum / self.routing_latency_ms_count
                if self.routing_latency_ms_count
                else 0.0
            )
            return {
                "routing_count": self.routing_count,
                "routing_success": self.routing_success,
                "routing_failures": self.routing_failures,
                "health_failures": self.health_failures,
                "no_capability_match": self.no_capability_match,
                "policy_exclusion": self.policy_exclusion,
                "fail_closed": self.fail_closed,
                "provider_selections": dict(self.provider_selections),
                "model_selections": dict(self.model_selections),
                "cost_class_distribution": dict(self.cost_class_distribution),
                "latency_class_distribution": dict(self.latency_class_distribution),
                "failure_codes": dict(self.failure_codes),
                "routing_latency_ms_avg": round(avg, 3),
                "routing_latency_ms_count": self.routing_latency_ms_count,
            }

    def render_prometheus(self) -> str:
        """Prometheus text with bounded labels only."""
        with self._lock:
            lines = [
                "# HELP air_routing_total AIR routing decisions attempted",
                "# TYPE air_routing_total counter",
                f"air_routing_total {self.routing_count}",
                "# HELP air_routing_success_total Successful AIR selections",
                "# TYPE air_routing_success_total counter",
                f"air_routing_success_total {self.routing_success}",
                "# HELP air_routing_failure_total Failed AIR selections (fail-closed)",
                "# TYPE air_routing_failure_total counter",
                f"air_routing_failure_total {self.routing_failures}",
                "# HELP air_provider_selection_total Selections by bounded provider label",
                "# TYPE air_provider_selection_total counter",
            ]
            for provider, n in sorted(self.provider_selections.items()):
                lines.append(f'air_provider_selection_total{{provider="{provider}"}} {n}')
            lines.extend(
                [
                    "# HELP air_model_selection_total Selections by bounded model label",
                    "# TYPE air_model_selection_total counter",
                ]
            )
            for model, n in sorted(self.model_selections.items()):
                lines.append(f'air_model_selection_total{{model="{model}"}} {n}')
            lines.extend(
                [
                    "# HELP air_no_capability_match_total Capability-match failures",
                    "# TYPE air_no_capability_match_total counter",
                    f"air_no_capability_match_total {self.no_capability_match}",
                    "# HELP air_provider_unhealthy_total Unhealthy-candidate failures",
                    "# TYPE air_provider_unhealthy_total counter",
                    f"air_provider_unhealthy_total {self.health_failures}",
                    "# HELP air_policy_exclusion_total Policy exclusion failures",
                    "# TYPE air_policy_exclusion_total counter",
                    f"air_policy_exclusion_total {self.policy_exclusion}",
                    "# HELP air_fail_closed_total Fail-closed routing outcomes",
                    "# TYPE air_fail_closed_total counter",
                    f"air_fail_closed_total {self.fail_closed}",
                    "# HELP air_routing_latency_ms Routing decision latency",
                    "# TYPE air_routing_latency_ms summary",
                    f"air_routing_latency_ms_sum {self.routing_latency_ms_sum}",
                    f"air_routing_latency_ms_count {self.routing_latency_ms_count}",
                ]
            )
            return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self.routing_count = 0
            self.routing_success = 0
            self.routing_failures = 0
            self.health_failures = 0
            self.no_capability_match = 0
            self.policy_exclusion = 0
            self.fail_closed = 0
            self.provider_selections.clear()
            self.model_selections.clear()
            self.cost_class_distribution.clear()
            self.latency_class_distribution.clear()
            self.failure_codes.clear()
            self.routing_latency_ms_sum = 0
            self.routing_latency_ms_count = 0


# Process-wide registry shared by engine + /metrics exposition.
AIR_METRICS = AirMetrics()


def cost_class_value(value: CostClass | str) -> str:
    return value.value if isinstance(value, CostClass) else str(value)


def latency_class_value(value: LatencyClass | str) -> str:
    return value.value if isinstance(value, LatencyClass) else str(value)


def monotonic_ms() -> int:
    return int(time.perf_counter() * 1000)
