"""Production configuration validation — deterministic startup report inputs."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


UNSAFE_PRODUCTION_DEFAULTS = (
    "COBRA_CORE_DEBUG",
    "COBRA_CORE_ALLOW_INSECURE",
    "PASF_REQUIRE_ORG_HEADER",  # false is unsafe if production ever enabled
)


@dataclass(frozen=True)
class ProductionConfig:
    enabled: bool = True
    # Production enablement remains disabled for KC-037.
    production_enabled: bool = False
    abort_on_critical: bool = True
    backup_root: str = ""
    migration_root: str = ""
    require_auth_secret: bool = True
    require_vault_url: bool = False  # staging may run without live vault
    max_startup_seconds: float = 60.0


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_production_config(env: dict[str, str] | None = None) -> ProductionConfig:
    e = env if env is not None else os.environ
    # Hard-lock: production_enabled never true from this milestone.
    return ProductionConfig(
        enabled=_bool(e.get("PRHF_ENABLED"), True),
        production_enabled=False,
        abort_on_critical=_bool(e.get("PRHF_ABORT_ON_CRITICAL"), True),
        backup_root=(e.get("PRHF_BACKUP_ROOT") or "").strip(),
        migration_root=(e.get("PRHF_MIGRATION_ROOT") or "").strip(),
        require_auth_secret=_bool(e.get("PRHF_REQUIRE_AUTH_SECRET"), True),
        require_vault_url=_bool(e.get("PRHF_REQUIRE_VAULT_URL"), False),
        max_startup_seconds=float((e.get("PRHF_MAX_STARTUP_SECONDS") or "60").strip() or "60"),
    )


@dataclass
class ConfigFinding:
    code: str
    severity: str  # critical | warning | info
    message: str
    key: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "key": self.key,
        }


def validate_configuration(env: dict[str, str] | None = None) -> list[ConfigFinding]:
    """Verify missing values, invalid ranges, deprecated/unsafe defaults."""
    e = env if env is not None else dict(os.environ)
    findings: list[ConfigFinding] = []
    cfg = load_production_config(e)

    secret = (e.get("COBRA_CORE_AUTH_SECRET") or "").strip()
    if cfg.require_auth_secret and not secret:
        findings.append(
            ConfigFinding(
                code="missing_secret",
                severity="critical",
                message="COBRA_CORE_AUTH_SECRET is required",
                key="COBRA_CORE_AUTH_SECRET",
            )
        )
    elif secret and secret in {"changeme", "secret", "password", "test"}:
        findings.append(
            ConfigFinding(
                code="weak_secret",
                severity="critical",
                message="COBRA_CORE_AUTH_SECRET uses an unsafe default value",
                key="COBRA_CORE_AUTH_SECRET",
            )
        )

    if _bool(e.get("COBRA_CORE_PRODUCTION"), False) or _bool(e.get("PRODUCTION_ENABLED"), False):
        findings.append(
            ConfigFinding(
                code="production_flag_set",
                severity="critical",
                message="Production enablement flags must remain disabled (KC-037)",
                key="COBRA_CORE_PRODUCTION",
            )
        )

    if _bool(e.get("COBRA_CORE_DEBUG"), False):
        findings.append(
            ConfigFinding(
                code="debug_enabled",
                severity="warning",
                message="COBRA_CORE_DEBUG is enabled — disable for production readiness",
                key="COBRA_CORE_DEBUG",
            )
        )

    vault = (e.get("EVIDENCE_VAULT_URL") or e.get("COBRA_VAULT_URL") or "").strip()
    if cfg.require_vault_url and not vault:
        findings.append(
            ConfigFinding(
                code="missing_vault_url",
                severity="critical",
                message="Vault URL required but not configured",
                key="EVIDENCE_VAULT_URL",
            )
        )

    # Duplicate / conflicting kill-switch semantics
    if e.get("COBRA_CORE_ENABLED") and e.get("COBRA_CORE_KILL_SWITCH"):
        en = _bool(e.get("COBRA_CORE_ENABLED"), True)
        kill = _bool(e.get("COBRA_CORE_KILL_SWITCH"), False)
        if en and kill:
            findings.append(
                ConfigFinding(
                    code="conflicting_kill_switch",
                    severity="warning",
                    message="COBRA_CORE_ENABLED=true conflicts with COBRA_CORE_KILL_SWITCH=true",
                    key="COBRA_CORE_KILL_SWITCH",
                )
            )

    # Invalid ranges
    for key, default in (
        ("PASF_ORG_RATE_LIMIT", "600"),
        ("PASF_CLIENT_RATE_LIMIT", "120"),
        ("ISPF_SESSION_TTL_SECONDS", "3600"),
    ):
        raw = (e.get(key) or default).strip()
        try:
            n = int(raw)
            if n < 1:
                raise ValueError("range")
        except ValueError:
            findings.append(
                ConfigFinding(
                    code="invalid_range",
                    severity="critical",
                    message=f"{key} must be a positive integer",
                    key=key,
                )
            )

    deprecated = [k for k in e if k.startswith("COBRA_LEGACY_") or k.endswith("_DEPRECATED")]
    for key in sorted(deprecated):
        findings.append(
            ConfigFinding(
                code="deprecated_setting",
                severity="warning",
                message=f"deprecated setting present: {key}",
                key=key,
            )
        )

    if cfg.production_enabled:
        findings.append(
            ConfigFinding(
                code="unsafe_production_default",
                severity="critical",
                message="production_enabled must remain false",
                key="PRHF",
            )
        )

    return findings
