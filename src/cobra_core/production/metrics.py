"""Production readiness metrics."""

from __future__ import annotations

import threading
from typing import Any


class ProductionMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.startup_duration = 0.0
        self.health_failures = 0
        self.backup_success = 0
        self.backup_failure = 0
        self.restore_success = 0
        self.restore_failure = 0
        self.migration_success = 0
        self.migration_failure = 0
        self.configuration_errors = 0
        self.performance_samples = 0

    def clear(self) -> None:
        with self._lock:
            self.startup_duration = 0.0
            self.health_failures = 0
            self.backup_success = 0
            self.backup_failure = 0
            self.restore_success = 0
            self.restore_failure = 0
            self.migration_success = 0
            self.migration_failure = 0
            self.configuration_errors = 0
            self.performance_samples = 0

    def set_startup_duration(self, seconds: float) -> None:
        with self._lock:
            self.startup_duration = max(0.0, float(seconds))

    def incr(self, name: str, *, amount: int = 1) -> None:
        with self._lock:
            if hasattr(self, name):
                setattr(self, name, getattr(self, name) + amount)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "startup_duration": round(self.startup_duration, 4),
                "health_failures": self.health_failures,
                "backup_success": self.backup_success,
                "backup_failure": self.backup_failure,
                "restore_success": self.restore_success,
                "restore_failure": self.restore_failure,
                "migration_success": self.migration_success,
                "migration_failure": self.migration_failure,
                "configuration_errors": self.configuration_errors,
                "performance_samples": self.performance_samples,
            }


PRODUCTION_METRICS = ProductionMetrics()
