"""KEF HTTP helpers (authenticated routes mount these via Protocol V1)."""

from __future__ import annotations

from typing import Any

from cobra_core.kef.audit import KEF_AUDIT
from cobra_core.kef.config import load_kef_config
from cobra_core.kef.metrics import KEF_METRICS
from cobra_core.kef.registry import CONNECTOR_REGISTRY


def handle_kef_metrics_json() -> dict[str, Any]:
    return {"ok": True, "metrics": KEF_METRICS.snapshot()}


def handle_kef_audit(*, limit: int = 50) -> dict[str, Any]:
    return {"ok": True, "entries": KEF_AUDIT.recent(limit=min(max(limit, 1), 200))}


def handle_kef_connectors() -> dict[str, Any]:
    return {
        "ok": True,
        "connectors": CONNECTOR_REGISTRY.list_ids(),
        "health": CONNECTOR_REGISTRY.health_snapshot(),
    }


def handle_kef_status() -> dict[str, Any]:
    config = load_kef_config()
    health = CONNECTOR_REGISTRY.health_snapshot()
    return {
        "ok": config.enabled,
        "enabled": config.enabled,
        "vault_enabled": config.vault_enabled,
        "connectors": health,
    }


def handle_vault_health() -> dict[str, Any]:
    try:
        vault = CONNECTOR_REGISTRY.get("evidence_vault")
        status = vault.health()
        value = getattr(status, "value", str(status))
    except Exception:
        value = "unavailable"
    return {"ok": value == "healthy", "health": value}
