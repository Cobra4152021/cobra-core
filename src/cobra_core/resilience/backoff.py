"""Bounded exponential backoff with optional deterministic jitter."""

from __future__ import annotations

import random
from random import Random


def compute_backoff_ms(
    attempt_index: int,
    *,
    initial_ms: int,
    max_ms: int,
    retry_after_ms: int | None = None,
    remaining_deadline_ms: int,
    rng: Random | None = None,
) -> int:
    """
    Return sleep ms for attempt_index (0-based after first failure).

    Honors Retry-After when within policy and remaining deadline.
    Never exceeds remaining_deadline_ms.
    """
    if remaining_deadline_ms <= 0:
        return 0
    if retry_after_ms is not None and retry_after_ms >= 0:
        base = min(retry_after_ms, max_ms)
    else:
        base = min(max_ms, initial_ms * (2 ** max(0, attempt_index)))
    r = rng or random.Random()
    # Full jitter in [0, base]
    jittered = int(r.uniform(0, max(0, base)))
    return max(0, min(jittered, remaining_deadline_ms, max_ms))
