"""Expanded health model — readiness, liveness, dependencies, degraded, maintenance."""

from __future__ import annotations

import time
from enum import StrEnum
from typing import Any


class HealthMode(StrEnum):
    READY = "ready"
    LIVE = "live"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    NOT_READY = "not_ready"


def _ops_overall() -> str:
    try:
        from cobra_core.operations.health import overall_status

        return overall_status().value
    except Exception:  # noqa: BLE001
        return "offline"


def _maintenance_active() -> bool:
    try:
        from cobra_core.operations.maintenance import MAINTENANCE

        return bool(MAINTENANCE.state().active)
    except Exception:  # noqa: BLE001
        return False


def liveness() -> dict[str, Any]:
    """Process is up."""
    return {"ok": True, "mode": HealthMode.LIVE.value, "ts": time.time()}


def readiness(*, startup_ok: bool = True) -> dict[str, Any]:
    if _maintenance_active():
        return {
            "ok": False,
            "mode": HealthMode.MAINTENANCE.value,
            "reason": "maintenance",
            "ts": time.time(),
        }
    if not startup_ok:
        return {
            "ok": False,
            "mode": HealthMode.NOT_READY.value,
            "reason": "startup_validation_failed",
            "ts": time.time(),
        }
    overall = _ops_overall()
    if overall in {"offline"}:
        return {
            "ok": False,
            "mode": HealthMode.NOT_READY.value,
            "reason": overall,
            "ts": time.time(),
        }
    if overall in {"degraded", "maintenance"}:
        return {
            "ok": True,
            "mode": HealthMode.DEGRADED.value
            if overall == "degraded"
            else HealthMode.MAINTENANCE.value,
            "reason": overall,
            "ts": time.time(),
        }
    return {"ok": True, "mode": HealthMode.READY.value, "ts": time.time()}


def dependency_readiness() -> dict[str, Any]:
    deps: dict[str, Any] = {}
    # ISPF
    try:
        from cobra_core.security.config import load_security_config

        deps["ispf"] = {"ok": load_security_config().enabled}
    except Exception as exc:  # noqa: BLE001
        deps["ispf"] = {"ok": False, "error": type(exc).__name__}
    # MOTF
    try:
        from cobra_core.organizations.config import load_organizations_config

        deps["motf"] = {"ok": load_organizations_config().enabled}
    except Exception as exc:  # noqa: BLE001
        deps["motf"] = {"ok": False, "error": type(exc).__name__}
    # PASF
    try:
        from cobra_core.api.config import load_api_config

        deps["pasf"] = {"ok": load_api_config().enabled}
    except Exception as exc:  # noqa: BLE001
        deps["pasf"] = {"ok": False, "error": type(exc).__name__}
    # Vault URL presence (connectivity probed separately in diagnostics)
    import os

    vault = (
        os.environ.get("EVIDENCE_VAULT_URL") or os.environ.get("COBRA_VAULT_URL") or ""
    ).strip()
    deps["vault_config"] = {"ok": True, "configured": bool(vault)}
    ok = all(bool(v.get("ok")) for v in deps.values())
    return {"ok": ok, "dependencies": deps, "ts": time.time()}


def health_bundle(*, startup_ok: bool = True) -> dict[str, Any]:
    live = liveness()
    ready = readiness(startup_ok=startup_ok)
    deps = dependency_readiness()
    return {
        "ok": bool(live.get("ok") and ready.get("ok") and deps.get("ok")),
        "liveness": live,
        "readiness": ready,
        "dependencies": deps,
        "operations_overall": _ops_overall(),
        "maintenance": _maintenance_active(),
    }
