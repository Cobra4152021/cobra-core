"""
In-process admission control for Protocol V1 server (RC1).

Provides:
- global max concurrent inferences
- optional daily request quota (process-local; resets UTC midnight)
- acquire/release that never leaks slots on exception paths

Not a substitute for Worker/org allowlists (Computer-side). This protects the
Core process from overload.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class AdmissionDecision:
    allowed: bool
    code: str | None = None
    message: str | None = None


class AdmissionController:
    def __init__(
        self,
        *,
        max_concurrent: int = 1,
        daily_request_limit: int | None = None,
    ) -> None:
        if max_concurrent < 1:
            raise ValueError("max_concurrent must be >= 1")
        if daily_request_limit is not None and daily_request_limit < 1:
            raise ValueError("daily_request_limit must be >= 1 when set")
        self._max_concurrent = max_concurrent
        self._daily_limit = daily_request_limit
        self._lock = threading.Lock()
        self._active = 0
        self._day_key = _utc_day()
        self._day_count = 0

    @property
    def active(self) -> int:
        with self._lock:
            return self._active

    @property
    def day_count(self) -> int:
        with self._lock:
            self._roll_day_unlocked()
            return self._day_count

    def try_acquire(self) -> AdmissionDecision:
        with self._lock:
            self._roll_day_unlocked()
            if self._daily_limit is not None and self._day_count >= self._daily_limit:
                return AdmissionDecision(
                    allowed=False,
                    code="rate_limited",
                    message="Daily request quota exceeded",
                )
            if self._active >= self._max_concurrent:
                return AdmissionDecision(
                    allowed=False,
                    code="rate_limited",
                    message="Concurrency limit reached",
                )
            self._active += 1
            self._day_count += 1
            return AdmissionDecision(allowed=True)

    def release(self) -> None:
        with self._lock:
            if self._active > 0:
                self._active -= 1

    def reset_for_tests(self) -> None:
        with self._lock:
            self._active = 0
            self._day_key = _utc_day()
            self._day_count = 0

    def _roll_day_unlocked(self) -> None:
        today = _utc_day()
        if today != self._day_key:
            self._day_key = today
            self._day_count = 0


def _utc_day() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d")
