"""Daily quota tracking with warning / soft / hard limits."""

from __future__ import annotations

import threading
import time
from datetime import UTC, datetime
from typing import Any

from cobra_core.operations.audit import OPERATIONS_AUDIT
from cobra_core.operations.config import OperationsConfig, load_operations_config
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.schemas import QuotaLimit, QuotaTier, QuotaUsage


def _day_key() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")


class QuotaTracker:
    COUNTERS = (
        "cases_per_day",
        "workflow_executions_per_day",
        "provider_calls_per_day",
        "vault_retrievals_per_day",
        "benchmark_runs_per_day",
    )

    def __init__(self, config: OperationsConfig | None = None) -> None:
        self.config = config or load_operations_config()
        self._lock = threading.Lock()
        self._day = _day_key()
        self._used: dict[str, int] = {k: 0 for k in self.COUNTERS}
        self._limits = self._build_limits(self.config)

    def _build_limits(self, config: OperationsConfig) -> dict[str, QuotaLimit]:
        mapping = {
            "cases_per_day": config.quota_cases_per_day,
            "workflow_executions_per_day": config.quota_workflows_per_day,
            "provider_calls_per_day": config.quota_provider_calls_per_day,
            "vault_retrievals_per_day": config.quota_vault_retrievals_per_day,
            "benchmark_runs_per_day": config.quota_benchmark_runs_per_day,
        }
        out: dict[str, QuotaLimit] = {}
        for name, hard in mapping.items():
            hard = max(0, int(hard))
            soft = int(hard * config.soft_ratio) if hard else 0
            warn = int(hard * config.warning_ratio) if hard else 0
            out[name] = QuotaLimit(name=name, warning=warn, soft_limit=soft, hard_limit=hard)
        return out

    def _roll_day(self) -> None:
        today = _day_key()
        if today != self._day:
            self._day = today
            self._used = {k: 0 for k in self.COUNTERS}

    def limits(self) -> dict[str, QuotaLimit]:
        with self._lock:
            return dict(self._limits)

    def set_hard_limit(self, name: str, hard: int, *, actor: str = "admin") -> QuotaLimit:
        key = name.strip()
        if key not in self.COUNTERS:
            raise KeyError(f"unknown quota: {key}")
        hard = max(0, int(hard))
        soft = int(hard * self.config.soft_ratio) if hard else 0
        warn = int(hard * self.config.warning_ratio) if hard else 0
        lim = QuotaLimit(name=key, warning=warn, soft_limit=soft, hard_limit=hard)
        with self._lock:
            self._limits[key] = lim
        OPERATIONS_AUDIT.record(
            "quota_change",
            actor=actor,
            quota=key,
            hard_limit=hard,
            soft_limit=soft,
            warning=warn,
        )
        return lim

    def _tier(self, used: int, lim: QuotaLimit) -> QuotaTier:
        if lim.hard_limit <= 0:
            return QuotaTier.OK
        if used >= lim.hard_limit:
            return QuotaTier.HARD_LIMIT
        if used >= lim.soft_limit:
            return QuotaTier.SOFT_LIMIT
        if used >= lim.warning:
            return QuotaTier.WARNING
        return QuotaTier.OK

    def usage(self, name: str) -> QuotaUsage:
        with self._lock:
            self._roll_day()
            lim = self._limits[name]
            used = self._used.get(name, 0)
            tier = self._tier(used, lim)
        return QuotaUsage(
            name=name,
            used=used,
            warning=lim.warning,
            soft_limit=lim.soft_limit,
            hard_limit=lim.hard_limit,
            tier=tier,
        )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            self._roll_day()
            day = self._day
            items = []
            for name in self.COUNTERS:
                lim = self._limits[name]
                used = self._used[name]
                items.append(
                    {
                        "name": name,
                        "used": used,
                        "warning": lim.warning,
                        "soft_limit": lim.soft_limit,
                        "hard_limit": lim.hard_limit,
                        "tier": self._tier(used, lim).value,
                    }
                )
        return {"day": day, "quotas": items, "checked_at": time.time()}

    def consume(self, name: str, amount: int = 1) -> QuotaUsage:
        """
        Increment usage. Hard limit still increments but callers should deny writes.
        Soft/warning are informational.
        """
        if name not in self.COUNTERS:
            raise KeyError(f"unknown quota: {name}")
        amount = max(0, int(amount))
        with self._lock:
            self._roll_day()
            self._used[name] = self._used.get(name, 0) + amount
            lim = self._limits[name]
            used = self._used[name]
            tier = self._tier(used, lim)
        if tier == QuotaTier.HARD_LIMIT:
            OPERATIONS_METRICS.record_quota_exceeded()
            OPERATIONS_AUDIT.record(
                "quota_exceeded",
                actor="system",
                quota=name,
                used=used,
                hard_limit=lim.hard_limit,
            )
        return QuotaUsage(
            name=name,
            used=used,
            warning=lim.warning,
            soft_limit=lim.soft_limit,
            hard_limit=lim.hard_limit,
            tier=tier,
        )

    def allow(self, name: str, amount: int = 1) -> bool:
        """True if consuming `amount` would not exceed hard limit (or unlimited)."""
        with self._lock:
            self._roll_day()
            lim = self._limits[name]
            if lim.hard_limit <= 0:
                return True
            return (self._used.get(name, 0) + max(0, amount)) <= lim.hard_limit

    def reset_for_tests(self) -> None:
        with self._lock:
            self._day = _day_key()
            self._used = {k: 0 for k in self.COUNTERS}
            self._limits = self._build_limits(self.config)


QUOTAS = QuotaTracker()
