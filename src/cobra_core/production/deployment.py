"""Deployment helpers — certification phases and readiness gates (no cloud deploy)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.startup import last_startup_report, run_startup_validation


class CertificationPhase(StrEnum):
    PHASE_1_LOCAL = "phase_1_local_validation"
    PHASE_2_OFFLINE_STAGING = "phase_2_offline_staging"
    PHASE_3_PERFORMANCE = "phase_3_performance"
    PHASE_4_SECURITY = "phase_4_security_review"
    PHASE_5_RECOVERY = "phase_5_recovery_testing"
    PHASE_6_MIGRATION = "phase_6_migration_testing"
    PHASE_7_SOAK = "phase_7_soak_24h"
    PHASE_8_ROLLBACK = "phase_8_rollback"


CERTIFICATION_PHASES: tuple[str, ...] = tuple(p.value for p in CertificationPhase)


def deployment_status() -> dict[str, Any]:
    report = last_startup_report()
    return {
        "ok": True,
        "production_enabled": False,
        "framework": "prhf",
        "certification_phases": list(CERTIFICATION_PHASES),
        "startup": report.public_dict() if report else None,
        "notes": [
            "Production enablement remains disabled (KC-037).",
            "No Kubernetes / auto-scaling / cloud-specific deploy in this milestone.",
        ],
    }


def run_local_validation_phase() -> dict[str, Any]:
    """Phase 1 — local validation."""
    report = run_startup_validation(correlation_id="phase_1")
    PRODUCTION_AUDIT.record(
        "certification_phase",
        phase=CertificationPhase.PHASE_1_LOCAL.value,
        result="ok" if report.ok else "failed",
    )
    return {
        "phase": CertificationPhase.PHASE_1_LOCAL.value,
        "ok": report.ok,
        "startup": report.public_dict(),
    }


def enter_maintenance(*, actor: str = "admin", reason: str = "deployment") -> dict[str, Any]:
    from cobra_core.operations.maintenance import MAINTENANCE

    MAINTENANCE.enter(actor=actor, reason=reason, reject_new_workflows=True)
    PRODUCTION_AUDIT.record("maintenance", actor=actor, result="enter", reason=reason)
    return {"ok": True, "maintenance": True, "reason": reason}


def exit_maintenance(*, actor: str = "admin") -> dict[str, Any]:
    from cobra_core.operations.maintenance import MAINTENANCE

    MAINTENANCE.exit(actor=actor)
    PRODUCTION_AUDIT.record("maintenance", actor=actor, result="exit")
    return {"ok": True, "maintenance": False}
