"""Versioned feature flag registry with audited changes."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

from cobra_core.operations.audit import OPERATIONS_AUDIT
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.schemas import FeatureFlag

# Canonical flag names (KC-032).
KNOWN_FLAGS: dict[str, str] = {
    "CASES_ENABLED": "Case management writes/reads (KC-031)",
    "WORKFLOWS_ENABLED": "Workflow engine execution (KC-029)",
    "KEF_ENABLED": "Knowledge & Evidence Framework",
    "BENCHMARK_ENABLED": "Investigation benchmark framework (KC-030)",
    "LIVE_PROVIDER_ENABLED": "Live provider path (CIAL live gate)",
    "READ_ONLY_MODE": "System-wide read-only (deny writes)",
    "ISF_ENABLED": "Investigation Skills Framework",
    "AIR_ENABLED": "Adaptive Intelligence Router",
    "RRF_ENABLED": "Reliability & Resilience Framework",
    "OCP_ENABLED": "Operations Control Plane",
}


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class FeatureFlagRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._flags: dict[str, FeatureFlag] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        defaults = {
            "CASES_ENABLED": False,
            "WORKFLOWS_ENABLED": False,
            "KEF_ENABLED": _env_bool("KEF_ENABLED", True),
            "BENCHMARK_ENABLED": _env_bool("BENCHMARK_ENABLED", True),
            "LIVE_PROVIDER_ENABLED": _env_bool("CIAL_LIVE_PROVIDER_ENABLED", False),
            "READ_ONLY_MODE": _env_bool("OCP_READ_ONLY_MODE", False),
            "ISF_ENABLED": _env_bool("ISF_ENABLED", True),
            "AIR_ENABLED": _env_bool("AIR_ENABLED", True),
            "RRF_ENABLED": _env_bool("RRF_ENABLED", True),
            "OCP_ENABLED": _env_bool("OCP_ENABLED", True),
        }
        now = time.time()
        for name, enabled in defaults.items():
            self._flags[name] = FeatureFlag(
                name=name,
                enabled=enabled,
                version=1,
                description=KNOWN_FLAGS.get(name, ""),
                updated_at=now,
                updated_by="bootstrap",
            )

    def get(self, name: str) -> FeatureFlag:
        key = name.strip().upper()
        with self._lock:
            if key not in self._flags:
                raise KeyError(f"unknown feature flag: {key}")
            return self._flags[key]

    def is_enabled(self, name: str) -> bool:
        return self.get(name).enabled

    def list_flags(self) -> list[FeatureFlag]:
        with self._lock:
            return [self._flags[k] for k in sorted(self._flags)]

    def set_flag(
        self,
        name: str,
        enabled: bool,
        *,
        actor: str = "admin",
        reason: str = "",
    ) -> FeatureFlag:
        key = name.strip().upper()
        with self._lock:
            if key not in self._flags:
                raise KeyError(f"unknown feature flag: {key}")
            prev = self._flags[key]
            if prev.enabled is bool(enabled):
                return prev
            nxt = FeatureFlag(
                name=key,
                enabled=bool(enabled),
                version=prev.version + 1,
                description=prev.description,
                updated_at=time.time(),
                updated_by=actor,
            )
            self._flags[key] = nxt
        OPERATIONS_METRICS.record_flag_change()
        OPERATIONS_AUDIT.record(
            "feature_flag_change",
            actor=actor,
            flag=key,
            enabled=bool(enabled),
            version=nxt.version,
            previous_version=prev.version,
            reason=reason[:200],
        )
        return nxt

    def snapshot(self) -> dict[str, Any]:
        return {
            "flags": [
                {
                    "name": f.name,
                    "enabled": f.enabled,
                    "version": f.version,
                    "description": f.description,
                    "updated_at": f.updated_at,
                    "updated_by": f.updated_by,
                }
                for f in self.list_flags()
            ]
        }

    def reset_for_tests(self) -> None:
        with self._lock:
            self._flags.clear()
            self._bootstrap()


FEATURE_FLAGS = FeatureFlagRegistry()


def read_only_mode() -> bool:
    return FEATURE_FLAGS.is_enabled("READ_ONLY_MODE")


def writes_allowed() -> bool:
    """False when read-only or maintenance rejects writes."""
    if read_only_mode():
        return False
    from cobra_core.operations.maintenance import MAINTENANCE

    if MAINTENANCE.state().active and MAINTENANCE.state().reject_new_workflows:
        return False
    return True
