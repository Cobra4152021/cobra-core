"""Pre-call budget protection (never call then check)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from cobra_core.resilience.config import ResilienceConfig
from cobra_core.resilience.errors import FailureCategory, ResilienceError
from cobra_core.resilience.prices import estimate_cost_usd


@dataclass
class BudgetLedger:
    """Process-scoped spend tracker (staging; not distributed)."""

    hourly_spent: float = 0.0
    daily_spent: float = 0.0
    hour_bucket: int = 0
    day_bucket: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def _roll(self) -> None:
        now = int(time.time())
        hour = now // 3600
        day = now // 86400
        if hour != self.hour_bucket:
            self.hour_bucket = hour
            self.hourly_spent = 0.0
        if day != self.day_bucket:
            self.day_bucket = day
            self.daily_spent = 0.0

    def remaining(self, cfg: ResilienceConfig, *, request_spent: float) -> dict[str, float]:
        with self._lock:
            self._roll()
            return {
                "request": max(0.0, cfg.max_estimated_cost_usd - request_spent),
                "hourly": max(0.0, cfg.hourly_budget_usd - self.hourly_spent),
                "daily": max(0.0, cfg.daily_budget_usd - self.daily_spent),
            }

    def assert_can_spend(
        self,
        cfg: ResilienceConfig,
        *,
        request_spent: float,
        estimated_next: float,
    ) -> None:
        rem = self.remaining(cfg, request_spent=request_spent)
        if estimated_next > rem["request"] + 1e-12:
            raise ResilienceError(FailureCategory.BUDGET_EXCEEDED, "request budget exceeded")
        if estimated_next > rem["hourly"] + 1e-12:
            raise ResilienceError(FailureCategory.BUDGET_EXCEEDED, "hourly budget exceeded")
        if estimated_next > rem["daily"] + 1e-12:
            raise ResilienceError(FailureCategory.BUDGET_EXCEEDED, "daily budget exceeded")

    def record(self, amount: float) -> None:
        with self._lock:
            self._roll()
            self.hourly_spent += max(0.0, amount)
            self.daily_spent += max(0.0, amount)

    def reset(self) -> None:
        with self._lock:
            self.hourly_spent = 0.0
            self.daily_spent = 0.0


GLOBAL_BUDGET = BudgetLedger()


def estimate_attempt_cost(
    provider_id: str,
    model_id: str,
    *,
    input_tokens: int,
    output_ceiling: int,
) -> float:
    return estimate_cost_usd(
        provider_id,
        model_id,
        input_tokens=input_tokens,
        output_tokens=output_ceiling,
    )
