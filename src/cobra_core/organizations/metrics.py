"""Per-organization MOTF metrics."""

from __future__ import annotations

import threading
from typing import Any


class OrganizationMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        # org_id → counters
        self._by_org: dict[str, dict[str, int | float]] = {}

    def clear(self) -> None:
        with self._lock:
            self._by_org.clear()

    def _bucket(self, organization_id: str) -> dict[str, int | float]:
        oid = organization_id.strip()
        if oid not in self._by_org:
            self._by_org[oid] = {
                "cases": 0,
                "workflows": 0,
                "users": 0,
                "evidence_retrieval": 0,
                "provider_usage": 0,
                "benchmark_runs": 0,
                "plugins": 0,
                "storage": 0,
            }
        return self._by_org[oid]

    def set_counts(self, organization_id: str, **counts: int | float) -> None:
        with self._lock:
            b = self._bucket(organization_id)
            for k, v in counts.items():
                if k in b:
                    b[k] = max(0, v)

    def incr(self, organization_id: str, key: str, *, amount: int | float = 1) -> None:
        with self._lock:
            b = self._bucket(organization_id)
            if key in b:
                b[key] = float(b[key]) + amount

    def snapshot(self, organization_id: str) -> dict[str, Any]:
        with self._lock:
            b = dict(self._bucket(organization_id))
            return {"organization_id": organization_id, **b}

    def all_snapshots(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {"organization_id": oid, **dict(vals)} for oid, vals in sorted(self._by_org.items())
            ]


ORGANIZATION_METRICS = OrganizationMetrics()
