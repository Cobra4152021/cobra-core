"""Isolated benchmark metrics (never mixed with production ISF/KEF counters)."""

from __future__ import annotations

import threading
from typing import Any


class BenchmarkMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.benchmark_runs = 0
        self.benchmark_pass = 0
        self.benchmark_fail = 0
        self.benchmark_latency_ms_sum = 0.0
        self.benchmark_latency_ms_count = 0
        self.benchmark_cost_usd_sum = 0.0
        self.benchmark_accuracy_sum = 0.0
        self.benchmark_accuracy_count = 0
        self.benchmark_repeatability_sum = 0.0
        self.benchmark_repeatability_count = 0

    def clear(self) -> None:
        with self._lock:
            self.benchmark_runs = 0
            self.benchmark_pass = 0
            self.benchmark_fail = 0
            self.benchmark_latency_ms_sum = 0.0
            self.benchmark_latency_ms_count = 0
            self.benchmark_cost_usd_sum = 0.0
            self.benchmark_accuracy_sum = 0.0
            self.benchmark_accuracy_count = 0
            self.benchmark_repeatability_sum = 0.0
            self.benchmark_repeatability_count = 0

    def record_run(
        self,
        *,
        passed: bool,
        overall_score: float,
        latency_avg_ms: float,
        cost_total_usd: float,
        repeatability_rate: float | None = None,
    ) -> None:
        with self._lock:
            self.benchmark_runs += 1
            if passed:
                self.benchmark_pass += 1
            else:
                self.benchmark_fail += 1
            self.benchmark_latency_ms_sum += float(latency_avg_ms)
            self.benchmark_latency_ms_count += 1
            self.benchmark_cost_usd_sum += float(cost_total_usd)
            self.benchmark_accuracy_sum += float(overall_score)
            self.benchmark_accuracy_count += 1
            if repeatability_rate is not None:
                self.benchmark_repeatability_sum += float(repeatability_rate)
                self.benchmark_repeatability_count += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            lat_n = max(self.benchmark_latency_ms_count, 1)
            acc_n = max(self.benchmark_accuracy_count, 1)
            rep_n = max(self.benchmark_repeatability_count, 1)
            return {
                "benchmark_runs": self.benchmark_runs,
                "benchmark_pass": self.benchmark_pass,
                "benchmark_fail": self.benchmark_fail,
                "benchmark_latency": round(
                    self.benchmark_latency_ms_sum / lat_n
                    if self.benchmark_latency_ms_count
                    else 0.0,
                    2,
                ),
                "benchmark_cost": round(self.benchmark_cost_usd_sum, 6),
                "benchmark_accuracy": round(
                    self.benchmark_accuracy_sum / acc_n if self.benchmark_accuracy_count else 0.0,
                    4,
                ),
                "benchmark_repeatability": round(
                    self.benchmark_repeatability_sum / rep_n
                    if self.benchmark_repeatability_count
                    else 0.0,
                    4,
                ),
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# HELP benchmark_runs Total isolated benchmark runs",
            "# TYPE benchmark_runs counter",
            f"benchmark_runs {s['benchmark_runs']}",
            "# HELP benchmark_pass Passed benchmark runs",
            "# TYPE benchmark_pass counter",
            f"benchmark_pass {s['benchmark_pass']}",
            "# HELP benchmark_fail Failed benchmark runs",
            "# TYPE benchmark_fail counter",
            f"benchmark_fail {s['benchmark_fail']}",
            "# HELP benchmark_latency Average benchmark latency ms",
            "# TYPE benchmark_latency gauge",
            f"benchmark_latency {s['benchmark_latency']}",
            "# HELP benchmark_cost Cumulative estimated benchmark cost USD",
            "# TYPE benchmark_cost counter",
            f"benchmark_cost {s['benchmark_cost']}",
            "# HELP benchmark_accuracy Average overall accuracy",
            "# TYPE benchmark_accuracy gauge",
            f"benchmark_accuracy {s['benchmark_accuracy']}",
            "# HELP benchmark_repeatability Average identical-output rate",
            "# TYPE benchmark_repeatability gauge",
            f"benchmark_repeatability {s['benchmark_repeatability']}",
        ]
        return "\n".join(lines) + "\n"


BENCHMARK_METRICS = BenchmarkMetrics()
