"""MOTF configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class OrganizationsConfig:
    enabled: bool = True
    # Cross-organization access denied by default.
    allow_cross_org: bool = False
    default_classification: str = "internal"
    policy_version: str = "motf-1"


def load_organizations_config(env: dict[str, str] | None = None) -> OrganizationsConfig:
    e = env if env is not None else os.environ
    return OrganizationsConfig(
        enabled=_bool(e.get("MOTF_ENABLED"), True),
        allow_cross_org=False,  # hard-locked — federation out of scope
        default_classification=(e.get("MOTF_DEFAULT_CLASSIFICATION") or "internal").strip(),
        policy_version=(e.get("MOTF_POLICY_VERSION") or "motf-1").strip() or "motf-1",
    )
