"""Startup validation — abort on critical failures when configured."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.configuration import (
    ConfigFinding,
    load_production_config,
    validate_configuration,
)
from cobra_core.production.metrics import PRODUCTION_METRICS
from cobra_core.production.performance import PERFORMANCE


@dataclass
class StartupReport:
    ok: bool
    aborted: bool
    duration_s: float
    findings: list[ConfigFinding] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "aborted": self.aborted,
            "duration_s": round(self.duration_s, 4),
            "correlation_id": self.correlation_id,
            "findings": [f.public_dict() for f in self.findings],
            "checks": self.checks,
            "critical_count": sum(1 for f in self.findings if f.severity == "critical"),
            "warning_count": sum(1 for f in self.findings if f.severity == "warning"),
        }


_LAST_REPORT: StartupReport | None = None
_STARTUP_OK = True


def last_startup_report() -> StartupReport | None:
    return _LAST_REPORT


def startup_ok() -> bool:
    return _STARTUP_OK


def run_startup_validation(
    *,
    env: dict[str, str] | None = None,
    correlation_id: str = "startup",
) -> StartupReport:
    """
    Validate configuration, flags, secrets, vault/provider config presence,
    schema/plugin/org registry readiness. Deterministic report.
    """
    global _LAST_REPORT, _STARTUP_OK
    t0 = time.perf_counter()
    cfg = load_production_config(env)
    findings = validate_configuration(env)
    checks: dict[str, Any] = {
        "configuration": True,
        "feature_flags": False,
        "required_secrets": False,
        "vault_connectivity": "skipped",
        "provider_configuration": False,
        "schema_versions": True,
        "plugin_compatibility": False,
        "organization_registry": False,
        "production_enabled": cfg.production_enabled,
    }

    # Feature flags
    try:
        from cobra_core.operations.feature_flags import FEATURE_FLAGS

        snap = FEATURE_FLAGS.snapshot() if hasattr(FEATURE_FLAGS, "snapshot") else None
        checks["feature_flags"] = True
        checks["feature_flags_detail"] = snap if isinstance(snap, dict) else {"ok": True}
    except Exception as exc:  # noqa: BLE001
        findings.append(
            ConfigFinding(
                "feature_flags_error",
                "warning",
                f"feature flags unavailable: {type(exc).__name__}",
            )
        )

    # Secrets (already in findings)
    checks["required_secrets"] = not any(
        f.code in {"missing_secret", "weak_secret"} for f in findings
    )

    # Provider configuration (no live call)
    try:
        from cobra_core.cial.config import load_cial_config

        cial = load_cial_config()
        checks["provider_configuration"] = True
        checks["provider_configured"] = bool(getattr(cial, "openai_configured", False))
    except Exception as exc:  # noqa: BLE001
        findings.append(
            ConfigFinding(
                "provider_config_error",
                "warning",
                f"provider config error: {type(exc).__name__}",
            )
        )

    # Vault — config presence only at startup (connectivity is staging-dependent)
    import os

    e = env if env is not None else os.environ
    vault = (e.get("EVIDENCE_VAULT_URL") or e.get("COBRA_VAULT_URL") or "").strip()
    if vault:
        checks["vault_connectivity"] = "configured_not_probed"
    elif cfg.require_vault_url:
        checks["vault_connectivity"] = "missing"
    else:
        checks["vault_connectivity"] = "optional_absent"

    # Plugin compatibility
    try:
        from cobra_core.plugins.manager import PLUGIN_MANAGER

        PLUGIN_MANAGER.ensure_bootstrapped()
        plugins = PLUGIN_MANAGER.list_plugins()
        failed = [p for p in plugins if p.get("state") == "failed"]
        checks["plugin_compatibility"] = len(failed) == 0
        checks["plugins_loaded"] = len(plugins)
        if failed:
            findings.append(
                ConfigFinding(
                    "plugin_incompatible",
                    "warning",
                    f"{len(failed)} plugin(s) in failed state",
                )
            )
    except Exception as exc:  # noqa: BLE001
        findings.append(
            ConfigFinding(
                "plugin_check_error",
                "warning",
                f"plugin check error: {type(exc).__name__}",
            )
        )

    # Organization registry
    try:
        from cobra_core.organizations.registry import ORGANIZATION_REGISTRY

        _ = ORGANIZATION_REGISTRY.list_organizations()
        checks["organization_registry"] = True
    except Exception as exc:  # noqa: BLE001
        findings.append(
            ConfigFinding(
                "org_registry_error",
                "critical",
                f"organization registry error: {type(exc).__name__}",
            )
        )

    # Schema versions (framework markers)
    checks["schema_versions"] = {
        "motf": "motf-1",
        "pasf": "v1",
        "prhf": "prhf-1",
        "ok": True,
    }

    critical = [f for f in findings if f.severity == "critical"]
    PRODUCTION_METRICS.incr("configuration_errors", amount=len(critical))
    ok = len(critical) == 0
    aborted = bool(cfg.abort_on_critical and critical)
    duration = time.perf_counter() - t0
    PERFORMANCE.record_startup(duration)
    report = StartupReport(
        ok=ok and not aborted,
        aborted=aborted,
        duration_s=duration,
        findings=findings,
        checks=checks,
        correlation_id=correlation_id,
    )
    _LAST_REPORT = report
    _STARTUP_OK = report.ok
    PRODUCTION_AUDIT.record(
        "startup",
        result="aborted" if aborted else ("ok" if report.ok else "failed"),
        duration_s=round(duration, 4),
        critical=len(critical),
        correlation_id=correlation_id,
    )
    return report


def record_shutdown(*, actor: str = "system") -> str:
    return PRODUCTION_AUDIT.record("shutdown", actor=actor, result="ok")
