"""Authenticated Operations Control Plane HTTP handlers."""

from __future__ import annotations

from typing import Any

from cobra_core.operations.alerts import alerts_public_dict
from cobra_core.operations.audit import OPERATIONS_AUDIT
from cobra_core.operations.feature_flags import FEATURE_FLAGS
from cobra_core.operations.health import health_public_dict
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.status import status_public_dict
from cobra_core.operations.usage import USAGE


def handle_operations_status() -> dict[str, Any]:
    return status_public_dict()


def handle_operations_health() -> dict[str, Any]:
    return health_public_dict()


def handle_operations_usage() -> dict[str, Any]:
    return {"ok": True, **USAGE.to_public_dict()}


def handle_operations_alerts() -> dict[str, Any]:
    return alerts_public_dict()


def handle_operations_feature_flags() -> dict[str, Any]:
    return {"ok": True, **FEATURE_FLAGS.snapshot()}


def handle_operations_metrics() -> dict[str, Any]:
    return {"ok": True, "metrics": OPERATIONS_METRICS.snapshot()}


def handle_operations_audit(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "entries": OPERATIONS_AUDIT.recent(limit=limit)}
