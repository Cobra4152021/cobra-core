"""CIAL configuration from environment (no secrets)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL

DEFAULT_PROVIDER = "mock"


class CialConfigError(ValueError):
    """Invalid CIAL configuration."""


@dataclass(frozen=True)
class CialConfig:
    """Safe CIAL defaults — mock provider, no credentials."""

    enabled: bool
    default_provider: str
    default_model: str
    routing_policy: RoutingPolicy


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def load_cial_config() -> CialConfig:
    """
    Load CIAL settings.

    Safe defaults preserve Internal Alpha mock behavior when enabled:
    provider=mock, model=cobra-core-qwen3-8b, policy=default.
    """
    policy_raw = (
        os.environ.get("CIAL_ROUTING_POLICY", "").strip().lower() or RoutingPolicy.DEFAULT.value
    )
    try:
        policy = RoutingPolicy(policy_raw)
    except ValueError as exc:
        raise CialConfigError(
            "CIAL_ROUTING_POLICY must be one of: " + ", ".join(p.value for p in RoutingPolicy)
        ) from exc

    return CialConfig(
        enabled=_env_bool("CIAL_ENABLED", True),
        default_provider=(os.environ.get("CIAL_DEFAULT_PROVIDER", "").strip() or DEFAULT_PROVIDER),
        default_model=(os.environ.get("CIAL_DEFAULT_MODEL", "").strip() or DEFAULT_MODEL),
        routing_policy=policy,
    )
