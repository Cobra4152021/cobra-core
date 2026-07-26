"""Composite operations status (no secrets / evidence / case bodies)."""

from __future__ import annotations

from typing import Any

from cobra_core.operations.feature_flags import FEATURE_FLAGS, read_only_mode
from cobra_core.operations.health import health_public_dict, overall_status
from cobra_core.operations.maintenance import MAINTENANCE
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.quotas import QUOTAS
from cobra_core.operations.schemas import ComponentHealth


def status_public_dict() -> dict[str, Any]:
    health = health_public_dict()
    overall = health["overall"]
    return {
        "ok": True,
        "overall": overall,
        "read_only_mode": read_only_mode(),
        "maintenance": MAINTENANCE.snapshot(),
        "feature_flags_summary": {
            f["name"]: {"enabled": f["enabled"], "version": f["version"]}
            for f in FEATURE_FLAGS.snapshot()["flags"]
        },
        "quotas": QUOTAS.snapshot(),
        "metrics": OPERATIONS_METRICS.snapshot(),
        "health_overall": overall,
        "writes_allowed": (
            not read_only_mode()
            and MAINTENANCE.allow_new_workflow()
            and overall != ComponentHealth.OFFLINE.value
        ),
    }
