"""Operations Control Plane metrics (admin plane only)."""

from __future__ import annotations

import threading
from typing import Any


class OperationsMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.system_health_transitions = 0
        self.operations_alerts = 0
        self.feature_flag_changes = 0
        self.maintenance_events = 0
        self.quota_exceeded = 0
        self.active_cases = 0
        self.active_workflows = 0
        self.provider_utilization = 0.0

    def clear(self) -> None:
        with self._lock:
            self.system_health_transitions = 0
            self.operations_alerts = 0
            self.feature_flag_changes = 0
            self.maintenance_events = 0
            self.quota_exceeded = 0
            self.active_cases = 0
            self.active_workflows = 0
            self.provider_utilization = 0.0

    def record_health_transition(self) -> None:
        with self._lock:
            self.system_health_transitions += 1

    def record_alert(self) -> None:
        with self._lock:
            self.operations_alerts += 1

    def record_flag_change(self) -> None:
        with self._lock:
            self.feature_flag_changes += 1

    def record_maintenance(self) -> None:
        with self._lock:
            self.maintenance_events += 1

    def record_quota_exceeded(self) -> None:
        with self._lock:
            self.quota_exceeded += 1

    def set_active(self, *, cases: int | None = None, workflows: int | None = None) -> None:
        with self._lock:
            if cases is not None:
                self.active_cases = max(0, int(cases))
            if workflows is not None:
                self.active_workflows = max(0, int(workflows))

    def set_provider_utilization(self, value: float) -> None:
        with self._lock:
            self.provider_utilization = max(0.0, min(1.0, float(value)))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "system_health": self.system_health_transitions,
                "operations_alerts": self.operations_alerts,
                "feature_flag_changes": self.feature_flag_changes,
                "maintenance_events": self.maintenance_events,
                "quota_exceeded": self.quota_exceeded,
                "active_cases": self.active_cases,
                "active_workflows": self.active_workflows,
                "provider_utilization": round(self.provider_utilization, 4),
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# HELP system_health Health transition count",
            "# TYPE system_health counter",
            f"system_health {s['system_health']}",
            "# HELP operations_alerts Operational alerts generated",
            "# TYPE operations_alerts counter",
            f"operations_alerts {s['operations_alerts']}",
            "# HELP feature_flag_changes Feature flag change count",
            "# TYPE feature_flag_changes counter",
            f"feature_flag_changes {s['feature_flag_changes']}",
            "# HELP maintenance_events Maintenance enter/exit events",
            "# TYPE maintenance_events counter",
            f"maintenance_events {s['maintenance_events']}",
            "# HELP quota_exceeded Hard quota exceed events",
            "# TYPE quota_exceeded counter",
            f"quota_exceeded {s['quota_exceeded']}",
            "# HELP active_cases Active cases gauge",
            "# TYPE active_cases gauge",
            f"active_cases {s['active_cases']}",
            "# HELP active_workflows Active workflows gauge",
            "# TYPE active_workflows gauge",
            f"active_workflows {s['active_workflows']}",
            "# HELP provider_utilization Provider utilization 0-1",
            "# TYPE provider_utilization gauge",
            f"provider_utilization {s['provider_utilization']}",
        ]
        return "\n".join(lines) + "\n"


OPERATIONS_METRICS = OperationsMetrics()
