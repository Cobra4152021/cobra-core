"""Aggregate component health for the Operations Control Plane."""

from __future__ import annotations

import os
import time
from typing import Any

from cobra_core.operations.feature_flags import FEATURE_FLAGS
from cobra_core.operations.maintenance import MAINTENANCE
from cobra_core.operations.metrics import OPERATIONS_METRICS
from cobra_core.operations.schemas import ComponentHealth, ComponentHealthReport

_LAST_STATUSES: dict[str, ComponentHealth] = {}


def _report(component: str, status: ComponentHealth, detail: str = "") -> ComponentHealthReport:
    prev = _LAST_STATUSES.get(component)
    if prev is not None and prev != status:
        OPERATIONS_METRICS.record_health_transition()
        from cobra_core.operations.audit import OPERATIONS_AUDIT

        OPERATIONS_AUDIT.record(
            "health_transition",
            actor="system",
            component=component,
            from_status=prev.value,
            to_status=status.value,
        )
    _LAST_STATUSES[component] = status
    return ComponentHealthReport(
        component=component,
        status=status,
        detail=detail,
        checked_at=time.time(),
    )


def _flag_health(flag: str, *, present_detail: str) -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report(
            flag.lower().replace("_enabled", ""), ComponentHealth.MAINTENANCE, "maintenance"
        )
    # Map flag name to component id
    component = {
        "CASES_ENABLED": "cases",
        "WORKFLOWS_ENABLED": "workflows",
        "BENCHMARK_ENABLED": "benchmark",
    }.get(flag, flag.lower())
    if not FEATURE_FLAGS.is_enabled(flag):
        return _report(component, ComponentHealth.OFFLINE, f"{flag}=false")
    return _report(component, ComponentHealth.HEALTHY, present_detail)


def probe_computer() -> ComponentHealthReport:
    # Core process is up if OCP is evaluating.
    if MAINTENANCE.state().active:
        return _report("computer", ComponentHealth.MAINTENANCE, "maintenance mode")
    return _report("computer", ComponentHealth.HEALTHY, "process reachable")


def probe_isf() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("isf", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.isf.enabled import isf_enabled
        from cobra_core.isf.registry import SKILL_REGISTRY

        if not FEATURE_FLAGS.is_enabled("ISF_ENABLED") or not isf_enabled():
            return _report("isf", ComponentHealth.OFFLINE, "ISF disabled")
        n = len(SKILL_REGISTRY)
        if n < 1:
            return _report("isf", ComponentHealth.DEGRADED, "no skills registered")
        return _report("isf", ComponentHealth.HEALTHY, f"skills={n}")
    except Exception as exc:  # noqa: BLE001
        return _report("isf", ComponentHealth.OFFLINE, type(exc).__name__)


def probe_kef() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("kef", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.kef.config import kef_enabled, load_kef_config

        if not FEATURE_FLAGS.is_enabled("KEF_ENABLED") or not kef_enabled():
            return _report("kef", ComponentHealth.OFFLINE, "KEF disabled")
        cfg = load_kef_config()
        detail = f"vault_enabled={cfg.vault_enabled}"
        return _report("kef", ComponentHealth.HEALTHY, detail)
    except Exception as exc:  # noqa: BLE001
        return _report("kef", ComponentHealth.DEGRADED, type(exc).__name__)


def probe_evidence_vault() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("evidence_vault", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.kef.config import load_kef_config
        from cobra_core.kef.registry import CONNECTOR_REGISTRY

        cfg = load_kef_config()
        if not cfg.vault_enabled:
            return _report("evidence_vault", ComponentHealth.OFFLINE, "vault disabled")
        vault = CONNECTOR_REGISTRY.get("evidence_vault")
        status = vault.health()
        value = getattr(status, "value", str(status))
        if value == "healthy":
            return _report("evidence_vault", ComponentHealth.HEALTHY, "connector healthy")
        if value == "degraded":
            return _report("evidence_vault", ComponentHealth.DEGRADED, "connector degraded")
        return _report("evidence_vault", ComponentHealth.OFFLINE, value)
    except Exception as exc:  # noqa: BLE001
        return _report("evidence_vault", ComponentHealth.OFFLINE, type(exc).__name__)


def probe_air() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("air", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.cial.engine import _air_enabled

        if not FEATURE_FLAGS.is_enabled("AIR_ENABLED") or not _air_enabled():
            return _report("air", ComponentHealth.OFFLINE, "AIR disabled")
        return _report("air", ComponentHealth.HEALTHY, "enabled")
    except Exception as exc:  # noqa: BLE001
        return _report("air", ComponentHealth.DEGRADED, type(exc).__name__)


def probe_rrf() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("rrf", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.resilience.config import rrf_enabled

        if not FEATURE_FLAGS.is_enabled("RRF_ENABLED") or not rrf_enabled():
            return _report("rrf", ComponentHealth.OFFLINE, "RRF disabled")
        return _report("rrf", ComponentHealth.HEALTHY, "enabled")
    except Exception as exc:  # noqa: BLE001
        return _report("rrf", ComponentHealth.DEGRADED, type(exc).__name__)


def probe_cial() -> ComponentHealthReport:
    if MAINTENANCE.state().active:
        return _report("cial", ComponentHealth.MAINTENANCE, "maintenance")
    try:
        from cobra_core.cial.config import load_cial_config

        cfg = load_cial_config()
        if FEATURE_FLAGS.is_enabled("LIVE_PROVIDER_ENABLED") and not cfg.can_use_live_provider:
            return _report("cial", ComponentHealth.DEGRADED, "live flag on but live unavailable")
        return _report(
            "cial",
            ComponentHealth.HEALTHY,
            f"profile={cfg.active_profile};live={cfg.can_use_live_provider}",
        )
    except Exception as exc:  # noqa: BLE001
        return _report("cial", ComponentHealth.DEGRADED, type(exc).__name__)


def probe_benchmark() -> ComponentHealthReport:
    return _flag_health("BENCHMARK_ENABLED", present_detail="framework loaded")


def probe_cases() -> ComponentHealthReport:
    return _flag_health("CASES_ENABLED", present_detail="case management flag on")


def probe_workflows() -> ComponentHealthReport:
    return _flag_health("WORKFLOWS_ENABLED", present_detail="workflow engine flag on")


def probe_metrics() -> ComponentHealthReport:
    if MAINTENANCE.state().active and not MAINTENANCE.allow_metrics():
        return _report("metrics", ComponentHealth.MAINTENANCE, "metrics paused")
    return _report("metrics", ComponentHealth.HEALTHY, "operations metrics active")


def probe_audit() -> ComponentHealthReport:
    if MAINTENANCE.state().active and not MAINTENANCE.allow_audit():
        return _report("audit", ComponentHealth.MAINTENANCE, "audit paused")
    return _report("audit", ComponentHealth.HEALTHY, "operations audit active")


def collect_health() -> list[ComponentHealthReport]:
    return [
        probe_computer(),
        probe_cases(),
        probe_workflows(),
        probe_isf(),
        probe_kef(),
        probe_evidence_vault(),
        probe_air(),
        probe_rrf(),
        probe_cial(),
        probe_benchmark(),
        probe_metrics(),
        probe_audit(),
    ]


def overall_status(reports: list[ComponentHealthReport] | None = None) -> ComponentHealth:
    items = reports if reports is not None else collect_health()
    statuses = {r.status for r in items}
    if ComponentHealth.OFFLINE in statuses:
        # Partial offline of optional components should not fail whole system.
        critical = {
            r.status
            for r in items
            if r.component in {"computer", "isf", "air", "rrf", "cial", "metrics", "audit"}
        }
        if ComponentHealth.OFFLINE in critical:
            return ComponentHealth.OFFLINE
    if any(r.status == ComponentHealth.MAINTENANCE for r in items):
        return ComponentHealth.MAINTENANCE
    if any(r.status == ComponentHealth.DEGRADED for r in items):
        return ComponentHealth.DEGRADED
    return ComponentHealth.HEALTHY


def health_public_dict() -> dict[str, Any]:
    reports = collect_health()
    return {
        "ok": True,
        "overall": overall_status(reports).value,
        "app_env": os.environ.get("APP_ENV", "unknown"),
        "components": [
            {
                "component": r.component,
                "status": r.status.value,
                "detail": r.detail,
                "checked_at": r.checked_at,
            }
            for r in reports
        ],
    }


def reset_health_cache_for_tests() -> None:
    _LAST_STATUSES.clear()
