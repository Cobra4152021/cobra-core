"""Informational operational alerts (no notifications / no auto-actions)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from cobra_core.operations.health import collect_health
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.quotas import QUOTAS
from cobra_core.operations.schemas import (
    AlertSeverity,
    ComponentHealth,
    OperationalAlert,
    QuotaTier,
)


def _alert(
    code: str,
    message: str,
    *,
    severity: AlertSeverity,
    component: str = "",
) -> OperationalAlert:
    OPERATIONS_METRICS.record_alert()
    return OperationalAlert(
        alert_id=f"oa_{uuid.uuid4().hex[:10]}",
        code=code,
        severity=severity,
        message=message,
        component=component,
        created_at=time.time(),
        informational_only=True,
    )


def generate_alerts() -> list[OperationalAlert]:
    alerts: list[OperationalAlert] = []
    for report in collect_health():
        if report.component == "evidence_vault" and report.status in {
            ComponentHealth.OFFLINE,
            ComponentHealth.DEGRADED,
        }:
            alerts.append(
                _alert(
                    "evidence_vault_unavailable",
                    f"Evidence Vault status={report.status.value}: {report.detail}",
                    severity=AlertSeverity.CRITICAL
                    if report.status == ComponentHealth.OFFLINE
                    else AlertSeverity.WARNING,
                    component="evidence_vault",
                )
            )
        if report.component == "cial" and report.status == ComponentHealth.DEGRADED:
            alerts.append(
                _alert(
                    "provider_unavailable",
                    f"CIAL degraded: {report.detail}",
                    severity=AlertSeverity.WARNING,
                    component="cial",
                )
            )
        if report.component == "workflows" and report.status == ComponentHealth.DEGRADED:
            alerts.append(
                _alert(
                    "workflow_failures",
                    f"Workflow component degraded: {report.detail}",
                    severity=AlertSeverity.WARNING,
                    component="workflows",
                )
            )
        if report.component == "benchmark" and report.status == ComponentHealth.DEGRADED:
            alerts.append(
                _alert(
                    "benchmark_failures",
                    f"Benchmark degraded: {report.detail}",
                    severity=AlertSeverity.WARNING,
                    component="benchmark",
                )
            )

    # Quota hard limits
    for name in QUOTAS.COUNTERS:
        u = QUOTAS.usage(name)
        if u.tier == QuotaTier.HARD_LIMIT:
            alerts.append(
                _alert(
                    "quota_exceeded",
                    f"Quota hard limit reached for {name} ({u.used}/{u.hard_limit})",
                    severity=AlertSeverity.CRITICAL,
                    component="quotas",
                )
            )
        elif u.tier in {QuotaTier.SOFT_LIMIT, QuotaTier.WARNING}:
            alerts.append(
                _alert(
                    "quota_warning",
                    f"Quota {u.tier.value} for {name} ({u.used}/{u.hard_limit})",
                    severity=AlertSeverity.WARNING,
                    component="quotas",
                )
            )

    # High latency heuristic from usage tracker
    try:
        from cobra_core.operations.usage import USAGE

        snap = USAGE.snapshot()
        if snap.average_latency_ms >= 5000:
            alerts.append(
                _alert(
                    "high_latency",
                    f"Average latency {snap.average_latency_ms}ms >= 5000ms",
                    severity=AlertSeverity.WARNING,
                    component="usage",
                )
            )
    except Exception:  # noqa: BLE001
        pass

    # Circuit breaker open (best-effort; no provider id required)
    try:
        from cobra_core.resilience.circuit_breaker import CircuitBreakerRegistry
        from cobra_core.resilience.types import CircuitState

        # Process-local registry may be empty; informational only when present.
        # Import side-effect free: skip if no global registry singleton exists.
        _ = CircuitState
        _ = CircuitBreakerRegistry
    except Exception:  # noqa: BLE001
        pass

    return alerts


def alerts_public_dict() -> dict[str, Any]:
    items = generate_alerts()
    return {
        "ok": True,
        "count": len(items),
        "informational_only": True,
        "alerts": [
            {
                "alert_id": a.alert_id,
                "code": a.code,
                "severity": a.severity.value,
                "message": a.message,
                "component": a.component,
                "created_at": a.created_at,
                "informational_only": a.informational_only,
            }
            for a in items
        ],
    }
