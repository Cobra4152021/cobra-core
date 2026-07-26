"""Bounded retry decisions (no recursive loops)."""

from __future__ import annotations

from cobra_core.resilience.config import ResilienceConfig
from cobra_core.resilience.errors import FailureCategory, traits_for


def should_retry(
    category: FailureCategory,
    *,
    attempts_so_far: int,
    cfg: ResilienceConfig,
    remaining_deadline_ms: int,
    retry_after_ms: int | None = None,
) -> tuple[bool, str]:
    """
    attempts_so_far includes the failed attempt.
    max_attempts=2 → allow retry only when attempts_so_far < 2.
    """
    traits = traits_for(category)
    if not traits.retryable:
        return False, "not_retryable"
    if attempts_so_far >= cfg.max_attempts:
        return False, "max_attempts_exhausted"
    if remaining_deadline_ms <= 0:
        return False, "deadline_exceeded"
    if retry_after_ms is not None and retry_after_ms > remaining_deadline_ms:
        return False, "retry_after_exceeds_deadline"
    return True, "retry"
