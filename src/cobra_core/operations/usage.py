"""Usage aggregation for the operations plane (no case/evidence payloads)."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from typing import Any

from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.quotas import QUOTAS
from cobra_core.operations.schemas import UsageSnapshot


class UsageTracker:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._active_users = 0
        self._average_latency_ms = 0.0
        self._estimated_cost_usd = 0.0
        self._storage_growth_bytes = 0
        self._latency_samples = 0
        self._latency_sum = 0.0

    def set_active_users(self, count: int) -> None:
        with self._lock:
            self._active_users = max(0, int(count))

    def record_latency(self, latency_ms: float) -> None:
        with self._lock:
            self._latency_sum += max(0.0, float(latency_ms))
            self._latency_samples += 1
            self._average_latency_ms = self._latency_sum / self._latency_samples

    def add_cost(self, usd: float) -> None:
        with self._lock:
            self._estimated_cost_usd += max(0.0, float(usd))

    def set_storage_growth(self, nbytes: int) -> None:
        with self._lock:
            self._storage_growth_bytes = max(0, int(nbytes))

    def snapshot(self) -> UsageSnapshot:
        m = OPERATIONS_METRICS.snapshot()
        with self._lock:
            return UsageSnapshot(
                active_users=self._active_users,
                active_cases=int(m["active_cases"]),
                active_workflows=int(m["active_workflows"]),
                provider_utilization=float(m["provider_utilization"]),
                average_latency_ms=round(self._average_latency_ms, 2),
                estimated_cost_usd=round(self._estimated_cost_usd, 6),
                storage_growth_bytes=self._storage_growth_bytes,
                day_key=datetime.now(UTC).strftime("%Y-%m-%d"),
                extras={"quotas": QUOTAS.snapshot(), "checked_at": time.time()},
            )

    def to_public_dict(self) -> dict[str, Any]:
        s = self.snapshot()
        return {
            "active_users": s.active_users,
            "active_cases": s.active_cases,
            "active_workflows": s.active_workflows,
            "provider_utilization": s.provider_utilization,
            "average_latency_ms": s.average_latency_ms,
            "estimated_cost_usd": s.estimated_cost_usd,
            "storage_growth_bytes": s.storage_growth_bytes,
            "day_key": s.day_key,
            "quotas": s.extras.get("quotas"),
        }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._active_users = 0
            self._average_latency_ms = 0.0
            self._estimated_cost_usd = 0.0
            self._storage_growth_bytes = 0
            self._latency_samples = 0
            self._latency_sum = 0.0


USAGE = UsageTracker()
