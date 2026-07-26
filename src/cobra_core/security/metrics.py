"""ISPF metrics."""

from __future__ import annotations

import threading
from typing import Any


class SecurityMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.authorization_requests = 0
        self.authorization_denied = 0
        self.authorization_allowed = 0
        self.policy_evaluations = 0
        self.active_sessions = 0
        self.role_assignments = 0

    def clear(self) -> None:
        with self._lock:
            self.authorization_requests = 0
            self.authorization_denied = 0
            self.authorization_allowed = 0
            self.policy_evaluations = 0
            self.active_sessions = 0
            self.role_assignments = 0

    def record_authz(self, *, allowed: bool, policy_evals: int = 1) -> None:
        with self._lock:
            self.authorization_requests += 1
            self.policy_evaluations += max(0, policy_evals)
            if allowed:
                self.authorization_allowed += 1
            else:
                self.authorization_denied += 1

    def set_active_sessions(self, n: int) -> None:
        with self._lock:
            self.active_sessions = max(0, int(n))

    def set_role_assignments(self, n: int) -> None:
        with self._lock:
            self.role_assignments = max(0, int(n))

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "authorization_requests": self.authorization_requests,
                "authorization_denied": self.authorization_denied,
                "authorization_allowed": self.authorization_allowed,
                "policy_evaluations": self.policy_evaluations,
                "active_sessions": self.active_sessions,
                "role_assignments": self.role_assignments,
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        lines = []
        for key, val in s.items():
            lines.append(f"# HELP {key} ISPF metric")
            lines.append(f"# TYPE {key} gauge")
            lines.append(f"{key} {val}")
        lines.append("")
        return "\n".join(lines)


SECURITY_METRICS = SecurityMetrics()
