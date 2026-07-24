"""Monotonic timing helpers."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class Stopwatch:
    t0: float

    @classmethod
    def start(cls) -> Stopwatch:
        return cls(t0=time.perf_counter())

    def ms_since(self) -> int:
        return max(0, int(round((time.perf_counter() - self.t0) * 1000)))


def latency_block(
    *, queue_ms: int, provider_latency_ms: int, inference_ms: int, total_ms: int
) -> dict[str, int]:
    return {
        "queue_ms": int(queue_ms),
        "provider_latency_ms": int(provider_latency_ms),
        "inference_ms": int(inference_ms),
        "total_ms": int(total_ms),
    }
