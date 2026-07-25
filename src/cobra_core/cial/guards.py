"""Staging safeguards for live CIAL providers (fail closed; no billing)."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, date, datetime

from cobra_core.cial.config import CialConfig
from cobra_core.cial.errors import CialError, CialErrorCode
from cobra_core.cial.types import ModelRecord


@dataclass
class LiveGuardSnapshot:
    """Safe observability snapshot (no secrets / prompts)."""

    day: str
    daily_requests: int
    daily_estimated_cost: float
    inflight: int
    max_concurrent: int
    daily_request_quota: int | None
    daily_cost_ceiling: float | None


class LiveRequestGuard:
    """
    Process-local live-request controls.

    Enforces max input size, concurrency, daily request quota, and optional
    estimated-cost ceiling using configured (or unknown) model cost metadata.
    """

    def __init__(self, config: CialConfig) -> None:
        self.config = config
        self._lock = threading.Lock()
        self._day = date.today()
        self._daily_requests = 0
        self._daily_cost = 0.0
        self._inflight = 0

    def snapshot(self) -> LiveGuardSnapshot:
        with self._lock:
            self._roll_day_locked()
            return LiveGuardSnapshot(
                day=self._day.isoformat(),
                daily_requests=self._daily_requests,
                daily_estimated_cost=self._daily_cost,
                inflight=self._inflight,
                max_concurrent=self.config.live_max_concurrent,
                daily_request_quota=self.config.live_daily_request_quota,
                daily_cost_ceiling=self.config.live_daily_cost_ceiling,
            )

    def acquire(self, *, input_chars: int, max_tokens: int, model: ModelRecord) -> None:
        if input_chars > self.config.live_max_input_chars:
            raise CialError(
                CialErrorCode.QUOTA_EXCEEDED,
                "live provider input size limit exceeded",
            )
        if (
            self.config.live_max_output_tokens is not None
            and max_tokens > self.config.live_max_output_tokens
        ):
            raise CialError(
                CialErrorCode.QUOTA_EXCEEDED,
                "live provider output token limit exceeded",
            )

        with self._lock:
            self._roll_day_locked()
            if (
                self.config.live_daily_request_quota is not None
                and self._daily_requests >= self.config.live_daily_request_quota
            ):
                raise CialError(
                    CialErrorCode.QUOTA_EXCEEDED,
                    "live provider daily request quota exceeded",
                )
            if self._inflight >= self.config.live_max_concurrent:
                raise CialError(
                    CialErrorCode.RATE_LIMITED,
                    "live provider concurrency limit exceeded",
                )
            # Pre-check cost ceiling using configured estimates when available.
            est = _estimate_cost(
                model, prompt_tokens=max(1, input_chars // 4), completion_tokens=max_tokens
            )
            if (
                self.config.live_daily_cost_ceiling is not None
                and est is not None
                and self._daily_cost + est > self.config.live_daily_cost_ceiling
            ):
                raise CialError(
                    CialErrorCode.QUOTA_EXCEEDED,
                    "live provider daily estimated-cost ceiling exceeded",
                )
            self._inflight += 1
            self._daily_requests += 1

    def release(
        self,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        model: ModelRecord,
    ) -> None:
        with self._lock:
            self._roll_day_locked()
            self._inflight = max(0, self._inflight - 1)
            est = _estimate_cost(
                model, prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
            )
            if est is not None:
                self._daily_cost += est

    def _roll_day_locked(self) -> None:
        today = datetime.now(UTC).date()
        if today != self._day:
            self._day = today
            self._daily_requests = 0
            self._daily_cost = 0.0


def _estimate_cost(
    model: ModelRecord,
    *,
    prompt_tokens: int,
    completion_tokens: int,
) -> float | None:
    """Return estimated cost or None when pricing metadata is unknown."""
    if model.estimated_input_cost is None and model.estimated_output_cost is None:
        return None
    inp = float(model.estimated_input_cost or 0.0) * (prompt_tokens / 1000.0)
    out = float(model.estimated_output_cost or 0.0) * (completion_tokens / 1000.0)
    return inp + out
