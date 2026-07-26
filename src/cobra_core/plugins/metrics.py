"""Plugin framework metrics."""

from __future__ import annotations

import threading
from typing import Any


class PluginMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.plugins_loaded = 0
        self.plugins_enabled = 0
        self.plugin_failures = 0
        self.plugin_validation_errors = 0
        self.plugin_load_latency_ms_sum = 0.0
        self.plugin_load_latency_ms_count = 0

    def clear(self) -> None:
        with self._lock:
            self.plugins_loaded = 0
            self.plugins_enabled = 0
            self.plugin_failures = 0
            self.plugin_validation_errors = 0
            self.plugin_load_latency_ms_sum = 0.0
            self.plugin_load_latency_ms_count = 0

    def record_loaded(self, *, latency_ms: float) -> None:
        with self._lock:
            self.plugins_loaded += 1
            self.plugin_load_latency_ms_sum += max(0.0, float(latency_ms))
            self.plugin_load_latency_ms_count += 1

    def record_enabled(self, *, enabled: bool) -> None:
        with self._lock:
            if enabled:
                self.plugins_enabled += 1
            else:
                self.plugins_enabled = max(0, self.plugins_enabled - 1)

    def record_failure(self) -> None:
        with self._lock:
            self.plugin_failures += 1

    def record_validation_error(self) -> None:
        with self._lock:
            self.plugin_validation_errors += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            n = max(self.plugin_load_latency_ms_count, 1)
            return {
                "plugins_loaded": self.plugins_loaded,
                "plugins_enabled": self.plugins_enabled,
                "plugin_failures": self.plugin_failures,
                "plugin_validation_errors": self.plugin_validation_errors,
                "plugin_load_latency": round(
                    self.plugin_load_latency_ms_sum / n
                    if self.plugin_load_latency_ms_count
                    else 0.0,
                    2,
                ),
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        return "\n".join(
            [
                "# HELP plugins_loaded Plugins successfully loaded",
                "# TYPE plugins_loaded counter",
                f"plugins_loaded {s['plugins_loaded']}",
                "# HELP plugins_enabled Currently enabled plugins",
                "# TYPE plugins_enabled gauge",
                f"plugins_enabled {s['plugins_enabled']}",
                "# HELP plugin_failures Plugin load/enable failures",
                "# TYPE plugin_failures counter",
                f"plugin_failures {s['plugin_failures']}",
                "# HELP plugin_validation_errors Validation failures",
                "# TYPE plugin_validation_errors counter",
                f"plugin_validation_errors {s['plugin_validation_errors']}",
                "# HELP plugin_load_latency Average load latency ms",
                "# TYPE plugin_load_latency gauge",
                f"plugin_load_latency {s['plugin_load_latency']}",
                "",
            ]
        )


PLUGIN_METRICS = PluginMetrics()
