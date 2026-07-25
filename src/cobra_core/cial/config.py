"""CIAL configuration from environment (secrets never logged)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL

DEFAULT_PROVIDER = "mock"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_OPENAI_MAX_RETRIES = 2


class CialConfigError(ValueError):
    """Invalid CIAL configuration."""


@dataclass(frozen=True)
class CialConfig:
    """
    Safe CIAL defaults — mock provider unless explicitly configured.

    ``openai_api_key`` is process-local only; never serialize to Protocol V1,
    Computer, logs, or audit payloads.
    """

    enabled: bool
    default_provider: str
    default_model: str
    routing_policy: RoutingPolicy
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    openai_api_key: str = ""
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_timeout_seconds: float = DEFAULT_OPENAI_TIMEOUT_SECONDS
    openai_max_retries: int = DEFAULT_OPENAI_MAX_RETRIES

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    def __repr__(self) -> str:
        key_state = "set" if self.openai_api_key else "unset"
        return (
            "CialConfig("
            f"enabled={self.enabled!r}, "
            f"default_provider={self.default_provider!r}, "
            f"default_model={self.default_model!r}, "
            f"routing_policy={self.routing_policy!r}, "
            f"openai_base_url={self.openai_base_url!r}, "
            f"openai_api_key=<{key_state}>, "
            f"openai_model={self.openai_model!r}, "
            f"openai_timeout_seconds={self.openai_timeout_seconds!r}, "
            f"openai_max_retries={self.openai_max_retries!r})"
        )


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise CialConfigError(f"{name} must be a positive number") from exc
    if value <= 0:
        raise CialConfigError(f"{name} must be a positive number")
    return value


def _env_nonneg_int(name: str, default: int) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise CialConfigError(f"{name} must be a non-negative integer") from exc
    if value < 0:
        raise CialConfigError(f"{name} must be a non-negative integer")
    return value


def load_cial_config() -> CialConfig:
    """
    Load CIAL settings.

    Safe defaults preserve Internal Alpha mock behavior:
    provider=mock, model=cobra-core-qwen3-8b, policy=default.

    ``CIAL_PROVIDER`` aliases ``CIAL_DEFAULT_PROVIDER`` when set.
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

    provider = (
        os.environ.get("CIAL_PROVIDER", "").strip()
        or os.environ.get("CIAL_DEFAULT_PROVIDER", "").strip()
        or DEFAULT_PROVIDER
    ).lower()
    if provider not in {"mock", "openai"}:
        raise CialConfigError("CIAL_PROVIDER must be one of: mock, openai")

    openai_model = os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL
    default_model = os.environ.get("CIAL_DEFAULT_MODEL", "").strip()
    if not default_model:
        default_model = openai_model if provider == "openai" else DEFAULT_MODEL

    return CialConfig(
        enabled=_env_bool("CIAL_ENABLED", True),
        default_provider=provider,
        default_model=default_model,
        routing_policy=policy,
        openai_base_url=(os.environ.get("OPENAI_BASE_URL", "").strip() or DEFAULT_OPENAI_BASE_URL),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
        openai_model=openai_model,
        openai_timeout_seconds=_env_float("OPENAI_TIMEOUT_SECONDS", DEFAULT_OPENAI_TIMEOUT_SECONDS),
        openai_max_retries=_env_nonneg_int("OPENAI_MAX_RETRIES", DEFAULT_OPENAI_MAX_RETRIES),
    )
