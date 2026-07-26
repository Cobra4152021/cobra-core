"""Production diagnostics — correlation-friendly component probes (no secrets)."""

from __future__ import annotations

import time
import uuid
from typing import Any

from cobra_core.production.healthcheck import health_bundle
from cobra_core.production.integrity import integrity_report
from cobra_core.production.performance import PERFORMANCE


def run_diagnostics(*, correlation_id: str | None = None) -> dict[str, Any]:
    cid = correlation_id or f"diag_{uuid.uuid4().hex[:12]}"
    t0 = time.perf_counter()
    provider: dict[str, Any] = {"ok": True, "configured": False}
    vault: dict[str, Any] = {"ok": True, "configured": False, "probed": False}
    try:
        from cobra_core.cial.config import load_cial_config

        cfg = load_cial_config()
        provider = {
            "ok": True,
            "configured": bool(getattr(cfg, "openai_configured", False)),
            "note": "configuration only — no live provider call",
        }
    except Exception as exc:  # noqa: BLE001
        provider = {"ok": False, "error": type(exc).__name__}

    import os

    vault_url = (
        os.environ.get("EVIDENCE_VAULT_URL") or os.environ.get("COBRA_VAULT_URL") or ""
    ).strip()
    vault["configured"] = bool(vault_url)
    # Do not perform network vault calls here (deterministic offline diagnostics).

    plugins: dict[str, Any] = {"ok": True}
    try:
        from cobra_core.plugins.manager import PLUGIN_MANAGER

        PLUGIN_MANAGER.ensure_bootstrapped()
        plugins = {
            "ok": True,
            "count": len(PLUGIN_MANAGER.list_plugins()),
        }
    except Exception as exc:  # noqa: BLE001
        plugins = {"ok": False, "error": type(exc).__name__}

    orgs: dict[str, Any] = {"ok": True}
    try:
        from cobra_core.organizations.registry import ORGANIZATION_REGISTRY

        orgs = {"ok": True, "count": len(ORGANIZATION_REGISTRY.list_organizations())}
    except Exception as exc:  # noqa: BLE001
        orgs = {"ok": False, "error": type(exc).__name__}

    elapsed_ms = (time.perf_counter() - t0) * 1000
    PERFORMANCE.sample(request_latency_ms=elapsed_ms)
    return {
        "ok": bool(provider.get("ok") and plugins.get("ok") and orgs.get("ok")),
        "correlation_id": cid,
        "component_tracing": {
            "provider_config": provider,
            "vault_config": vault,
            "plugins": plugins,
            "organizations": orgs,
            "health": health_bundle(),
            "integrity": {
                "configuration_hash": integrity_report()["configuration_hash"],
                "openapi_checksum": integrity_report()["openapi_checksum"],
            },
        },
        "elapsed_ms": round(elapsed_ms, 2),
        "ts": time.time(),
    }
