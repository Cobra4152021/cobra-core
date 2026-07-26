"""Maintenance mode controller."""

from __future__ import annotations

import threading
import time
from typing import Any

from cobra_core.operations.audit import OPERATIONS_AUDIT
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.schemas import MaintenanceState


class MaintenanceController:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = MaintenanceState(active=False)
        self._draining_workflows = 0

    def state(self) -> MaintenanceState:
        with self._lock:
            return self._state

    def enter(
        self,
        *,
        actor: str = "admin",
        reason: str = "",
        drain_workflows: bool = True,
        reject_new_workflows: bool = True,
    ) -> MaintenanceState:
        with self._lock:
            self._state = MaintenanceState(
                active=True,
                entered_at=time.time(),
                entered_by=actor,
                reason=reason[:300],
                drain_workflows=drain_workflows,
                reject_new_workflows=reject_new_workflows,
                metrics_enabled=True,
                audit_enabled=True,
                reporting_enabled=True,
            )
            state = self._state
        OPERATIONS_METRICS.record_maintenance()
        OPERATIONS_AUDIT.record(
            "maintenance_enter",
            actor=actor,
            reason=reason[:300],
            drain_workflows=drain_workflows,
            reject_new_workflows=reject_new_workflows,
        )
        return state

    def exit(self, *, actor: str = "admin") -> MaintenanceState:
        with self._lock:
            was_active = self._state.active
            self._state = MaintenanceState(active=False)
            self._draining_workflows = 0
            state = self._state
        if was_active:
            OPERATIONS_METRICS.record_maintenance()
            OPERATIONS_AUDIT.record("maintenance_exit", actor=actor)
        return state

    def set_draining_count(self, count: int) -> None:
        with self._lock:
            self._draining_workflows = max(0, int(count))

    def draining_count(self) -> int:
        with self._lock:
            return self._draining_workflows

    def allow_new_workflow(self) -> bool:
        st = self.state()
        if not st.active:
            return True
        return not st.reject_new_workflows

    def allow_metrics(self) -> bool:
        return self.state().metrics_enabled

    def allow_audit(self) -> bool:
        return self.state().audit_enabled

    def allow_reporting(self) -> bool:
        return self.state().reporting_enabled

    def snapshot(self) -> dict[str, Any]:
        st = self.state()
        return {
            "active": st.active,
            "entered_at": st.entered_at,
            "entered_by": st.entered_by,
            "reason": st.reason,
            "drain_workflows": st.drain_workflows,
            "reject_new_workflows": st.reject_new_workflows,
            "draining_workflows": self.draining_count(),
            "metrics_enabled": st.metrics_enabled,
            "audit_enabled": st.audit_enabled,
            "reporting_enabled": st.reporting_enabled,
        }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._state = MaintenanceState(active=False)
            self._draining_workflows = 0


MAINTENANCE = MaintenanceController()
