"""Authoritative request deadline (never reset by child phases)."""

from __future__ import annotations

import time

from cobra_core.resilience.errors import FailureCategory, ResilienceError


class Deadline:
    def __init__(self, deadline_ms: int, *, start_mono: float | None = None) -> None:
        self.deadline_ms = max(0, int(deadline_ms))
        self._start = start_mono if start_mono is not None else time.monotonic()

    def remaining_ms(self) -> int:
        elapsed = (time.monotonic() - self._start) * 1000.0
        return max(0, int(self.deadline_ms - elapsed))

    def expired(self) -> bool:
        return self.remaining_ms() <= 0

    def assert_remaining(self, *, need_ms: int = 1) -> None:
        rem = self.remaining_ms()
        if rem < need_ms:
            raise ResilienceError(FailureCategory.REQUEST_DEADLINE_EXCEEDED)

    def child_timeout_ms(self, preferred_ms: int) -> int:
        """Cap preferred timeout by remaining deadline."""
        return max(0, min(int(preferred_ms), self.remaining_ms()))
