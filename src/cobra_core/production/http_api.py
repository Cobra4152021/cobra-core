"""Authenticated production readiness admin handlers (not part of /api/v1 PASF)."""

from __future__ import annotations

from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.deployment import deployment_status
from cobra_core.production.diagnostics import run_diagnostics
from cobra_core.production.healthcheck import health_bundle
from cobra_core.production.integrity import integrity_report
from cobra_core.production.metrics import PRODUCTION_METRICS
from cobra_core.production.migrations import MIGRATIONS
from cobra_core.production.performance import PERFORMANCE
from cobra_core.production.security_review import run_security_review
from cobra_core.production.startup import last_startup_report, run_startup_validation, startup_ok


def handle_production_status() -> dict[str, Any]:
    return deployment_status()


def handle_production_health() -> dict[str, Any]:
    return {"ok": True, "health": health_bundle(startup_ok=startup_ok())}


def handle_production_diagnostics() -> dict[str, Any]:
    return run_diagnostics()


def handle_production_startup_report() -> dict[str, Any]:
    report = last_startup_report() or run_startup_validation()
    return {"ok": report.ok, "startup": report.public_dict()}


def handle_production_metrics() -> dict[str, Any]:
    return {
        "ok": True,
        "metrics": PRODUCTION_METRICS.snapshot(),
        "performance": PERFORMANCE.snapshot(),
    }


def handle_production_integrity() -> dict[str, Any]:
    return integrity_report()


def handle_production_security_review() -> dict[str, Any]:
    return run_security_review()


def handle_production_migrations_dry_run() -> dict[str, Any]:
    return MIGRATIONS.dry_run()


def handle_production_audit(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "entries": PRODUCTION_AUDIT.recent(limit=limit)}
