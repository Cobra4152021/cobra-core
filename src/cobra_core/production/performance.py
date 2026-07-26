"""Performance sampling — startup, latency, memory/CPU (best-effort)."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.production.metrics import PRODUCTION_METRICS


def _memory_mb() -> float | None:
    try:
        import resource  # Unix

        usage = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is KB on Linux, bytes on macOS — report as best-effort MB
        return round(usage.ru_maxrss / 1024.0, 2)
    except Exception:  # noqa: BLE001
        try:
            import psutil  # type: ignore[import-untyped]  # optional

            return round(float(psutil.Process().memory_info().rss) / (1024 * 1024), 2)
        except Exception:  # noqa: BLE001
            return None


def _cpu_percent() -> float | None:
    try:
        import psutil  # optional

        return float(psutil.cpu_percent(interval=0.0))
    except Exception:  # noqa: BLE001
        return None


class PerformanceSampler:
    def __init__(self) -> None:
        self.startup_time_s: float | None = None
        self.samples: list[dict[str, Any]] = []

    def reset_for_tests(self) -> None:
        self.startup_time_s = None
        self.samples.clear()

    def record_startup(self, seconds: float) -> None:
        self.startup_time_s = max(0.0, float(seconds))
        PRODUCTION_METRICS.set_startup_duration(self.startup_time_s)

    def sample(
        self,
        *,
        request_latency_ms: float = 0.0,
        provider_latency_ms: float = 0.0,
        vault_latency_ms: float = 0.0,
        api_latency_ms: float = 0.0,
    ) -> dict[str, Any]:
        item = {
            "ts": time.time(),
            "request_latency_ms": request_latency_ms,
            "provider_latency_ms": provider_latency_ms,
            "vault_latency_ms": vault_latency_ms,
            "api_latency_ms": api_latency_ms,
            "memory_mb": _memory_mb(),
            "cpu_percent": _cpu_percent(),
            "startup_time_s": self.startup_time_s,
        }
        self.samples.append(item)
        if len(self.samples) > 500:
            self.samples = self.samples[-500:]
        PRODUCTION_METRICS.incr("performance_samples")
        return item

    def snapshot(self) -> dict[str, Any]:
        return {
            "startup_time_s": self.startup_time_s,
            "sample_count": len(self.samples),
            "latest": self.samples[-1] if self.samples else None,
            "memory_mb": _memory_mb(),
            "cpu_percent": _cpu_percent(),
        }


PERFORMANCE = PerformanceSampler()
