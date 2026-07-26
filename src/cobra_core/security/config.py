"""ISPF configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class SecurityConfig:
    enabled: bool = True
    # Default session TTL seconds (staging/dev).
    session_ttl_seconds: int = 3600
    # Deny by default when no allow policy matches.
    default_deny: bool = True
    # Explicit administrator role still requires assigned permissions (no bypass).
    admin_bypass: bool = False


def load_security_config(env: dict[str, str] | None = None) -> SecurityConfig:
    e = env if env is not None else os.environ
    ttl_raw = (e.get("ISPF_SESSION_TTL_SECONDS") or "3600").strip()
    try:
        ttl = max(60, int(ttl_raw))
    except ValueError:
        ttl = 3600
    return SecurityConfig(
        enabled=_bool(e.get("ISPF_ENABLED"), True),
        session_ttl_seconds=ttl,
        default_deny=_bool(e.get("ISPF_DEFAULT_DENY"), True),
        admin_bypass=False,  # hard-locked off — no implicit administrator bypass
    )
