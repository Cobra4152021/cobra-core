"""Public API configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class ApiConfig:
    enabled: bool = True
    org_rate_limit: int = 600
    client_rate_limit: int = 120
    rate_window_seconds: int = 60
    require_org_header: bool = False  # staging may set X-Cobra-Org-Id


def load_api_config(env: dict[str, str] | None = None) -> ApiConfig:
    e = env if env is not None else os.environ

    def _int(key: str, default: int) -> int:
        try:
            return max(1, int((e.get(key) or str(default)).strip()))
        except ValueError:
            return default

    return ApiConfig(
        enabled=_bool(e.get("PASF_ENABLED"), True),
        org_rate_limit=_int("PASF_ORG_RATE_LIMIT", 600),
        client_rate_limit=_int("PASF_CLIENT_RATE_LIMIT", 120),
        rate_window_seconds=_int("PASF_RATE_WINDOW_SECONDS", 60),
        require_org_header=_bool(e.get("PASF_REQUIRE_ORG_HEADER"), False),
    )
