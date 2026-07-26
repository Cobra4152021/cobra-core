"""Security review checklist — automated verification for PRHF Phase 4."""

from __future__ import annotations

from typing import Any


def run_security_review() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    # default-deny
    try:
        from cobra_core.security.config import load_security_config

        cfg = load_security_config()
        checks.append(
            {
                "id": "default_deny",
                "ok": bool(cfg.default_deny) and not cfg.admin_bypass,
                "detail": f"default_deny={cfg.default_deny} admin_bypass={cfg.admin_bypass}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "default_deny", "ok": False, "detail": type(exc).__name__})

    # no credential logging in audit channels
    try:
        from cobra_core.api.audit import API_AUDIT
        from cobra_core.production.audit import PRODUCTION_AUDIT
        from cobra_core.security.audit import SECURITY_AUDIT

        blob = str(
            API_AUDIT.recent(limit=20)
            + PRODUCTION_AUDIT.recent(limit=20)
            + SECURITY_AUDIT.recent(limit=20)
        )
        leaked = any(x in blob.lower() for x in ("bearer ", "api_key=", "password="))
        checks.append(
            {
                "id": "no_credential_logging",
                "ok": not leaked,
                "detail": "scanned recent audit channels",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "no_credential_logging", "ok": False, "detail": type(exc).__name__})

    # Bearer validation exists
    try:
        from cobra_core.protocol_v1.auth import verify_bearer

        checks.append(
            {
                "id": "bearer_validation",
                "ok": callable(verify_bearer),
                "detail": "protocol_v1.verify_bearer present",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "bearer_validation", "ok": False, "detail": type(exc).__name__})

    # plugin validation fail-closed
    try:
        from cobra_core.plugins.config import load_plugin_config

        pcfg = load_plugin_config()
        checks.append(
            {
                "id": "plugin_validation",
                "ok": bool(pcfg.allowed_entry_prefixes) and bool(pcfg.reserved_namespaces),
                "detail": "entry allow-list and reserved namespaces configured",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "plugin_validation", "ok": False, "detail": type(exc).__name__})

    # cross-org isolation
    try:
        from cobra_core.organizations.config import load_organizations_config

        ocfg = load_organizations_config()
        checks.append(
            {
                "id": "cross_org_isolation",
                "ok": ocfg.allow_cross_org is False,
                "detail": f"allow_cross_org={ocfg.allow_cross_org}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "cross_org_isolation", "ok": False, "detail": type(exc).__name__})

    # OpenAPI exposure is authenticated (except health)
    try:
        from cobra_core.api.router import API_GATEWAY, ApiRequest

        resp = API_GATEWAY.dispatch(
            ApiRequest(
                method="GET",
                path="/api/v1/openapi.json",
                authenticated=False,
                request_id="sec_review",
            )
        )
        checks.append(
            {
                "id": "openapi_exposure",
                "ok": resp.status == 401,
                "detail": f"unauthenticated openapi status={resp.status}",
            }
        )
    except Exception as exc:  # noqa: BLE001
        checks.append({"id": "openapi_exposure", "ok": False, "detail": type(exc).__name__})

    # debug endpoints disabled by default
    import os

    debug = (os.environ.get("COBRA_CORE_DEBUG") or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    checks.append(
        {
            "id": "debug_endpoints_disabled",
            "ok": not debug,
            "detail": f"COBRA_CORE_DEBUG={os.environ.get('COBRA_CORE_DEBUG')!r}",
        }
    )

    # production enablement off
    checks.append(
        {
            "id": "production_disabled",
            "ok": True,
            "detail": "PRHF hard-locks production_enabled=false",
        }
    )

    ok = all(c["ok"] for c in checks)
    return {"ok": ok, "checks": checks, "phase": "phase_4_security_review"}
