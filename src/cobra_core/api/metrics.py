"""Public API metrics."""

from __future__ import annotations

import threading
from typing import Any


class ApiMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.api_requests = 0
        self.api_errors = 0
        self.api_latency_ms_sum = 0.0
        self.api_latency_ms_count = 0
        self.api_rate_limits = 0
        self.sdk_versions: dict[str, int] = {}

    def clear(self) -> None:
        with self._lock:
            self.api_requests = 0
            self.api_errors = 0
            self.api_latency_ms_sum = 0.0
            self.api_latency_ms_count = 0
            self.api_rate_limits = 0
            self.sdk_versions.clear()

    def record_request(self, *, latency_ms: float, error: bool = False) -> None:
        with self._lock:
            self.api_requests += 1
            self.api_latency_ms_sum += max(0.0, latency_ms)
            self.api_latency_ms_count += 1
            if error:
                self.api_errors += 1

    def record_rate_limit(self) -> None:
        with self._lock:
            self.api_rate_limits += 1

    def record_sdk_version(self, version: str) -> None:
        key = (version or "unknown").strip() or "unknown"
        with self._lock:
            self.sdk_versions[key] = self.sdk_versions.get(key, 0) + 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            n = max(self.api_latency_ms_count, 1)
            return {
                "api_requests": self.api_requests,
                "api_errors": self.api_errors,
                "api_latency": round(
                    self.api_latency_ms_sum / n if self.api_latency_ms_count else 0.0,
                    2,
                ),
                "api_rate_limits": self.api_rate_limits,
                "sdk_versions": dict(sorted(self.sdk_versions.items())),
            }


API_METRICS = ApiMetrics()
