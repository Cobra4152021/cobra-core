"""CIAL configuration from environment (secrets never logged)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from cobra_core.cial.profiles import (
    BUILTIN_PROFILE_IDS,
    PROFILE_DEFAULT,
    InferenceProfile,
    legacy_provider_to_profile,
    resolve_profile,
)
from cobra_core.cial.types import RoutingPolicy
from cobra_core.protocol_v1.constants import DEFAULT_MODEL

DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_OPENAI_TIMEOUT_SECONDS = 60.0
DEFAULT_OPENAI_MAX_RETRIES = 2
DEFAULT_LIVE_MAX_INPUT_CHARS = 32_000
DEFAULT_LIVE_MAX_CONCURRENT = 1


class CialConfigError(ValueError):
    """Invalid CIAL configuration."""


@dataclass(frozen=True)
class CialConfig:
    """
    Profile-centric CIAL settings.

    External activation selects ``active_profile`` (default / offline / research).
    Provider/vendor bindings are resolved internally. ``openai_api_key`` is
    process-local only and never logged.
    """

    enabled: bool
    active_profile: str
    routing_policy: RoutingPolicy
    app_env: str = "staging"
    live_provider_enabled: bool = False
    openai_base_url: str = DEFAULT_OPENAI_BASE_URL
    openai_api_key: str = ""
    openai_model: str = DEFAULT_OPENAI_MODEL
    openai_timeout_seconds: float = DEFAULT_OPENAI_TIMEOUT_SECONDS
    openai_max_retries: int = DEFAULT_OPENAI_MAX_RETRIES
    live_max_input_chars: int = DEFAULT_LIVE_MAX_INPUT_CHARS
    live_max_output_tokens: int | None = None
    live_max_concurrent: int = DEFAULT_LIVE_MAX_CONCURRENT
    live_daily_request_quota: int | None = None
    live_daily_cost_ceiling: float | None = None
    mock_model: str = DEFAULT_MODEL

    def resolved_profile(self) -> InferenceProfile:
        return resolve_profile(
            self.active_profile,
            openai_model=self.openai_model,
            mock_model=self.mock_model,
        )

    @property
    def default_provider(self) -> str:
        """Internal provider id for the active profile (not an activation knob)."""
        return self.resolved_profile().provider_id

    @property
    def default_model(self) -> str:
        """Internal model id for the active profile."""
        return self.resolved_profile().model_id

    @property
    def openai_configured(self) -> bool:
        return bool(self.openai_api_key.strip())

    @property
    def is_staging(self) -> bool:
        return self.app_env.strip().lower() == "staging"

    @property
    def can_use_live_provider(self) -> bool:
        """
        Opt-in live inference gate for profiles that require a live backend.

        Requires staging + CIAL enabled + live flag + complete OpenAI config +
        a profile with ``requires_live`` (e.g. research). Production never activates.
        """
        profile = self.resolved_profile()
        return (
            self.is_staging
            and self.enabled
            and self.live_provider_enabled
            and self.openai_configured
            and profile.requires_live
        )

    def __repr__(self) -> str:
        key_state = "set" if self.openai_api_key else "unset"
        profile = self.resolved_profile()
        return (
            "CialConfig("
            f"enabled={self.enabled!r}, "
            f"app_env={self.app_env!r}, "
            f"active_profile={self.active_profile!r}, "
            f"resolved_provider={profile.provider_id!r}, "
            f"resolved_model={profile.model_id!r}, "
            f"live_provider_enabled={self.live_provider_enabled!r}, "
            f"can_use_live_provider={self.can_use_live_provider!r}, "
            f"routing_policy={self.routing_policy!r}, "
            f"openai_base_url={self.openai_base_url!r}, "
            f"openai_api_key=<{key_state}>, "
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


def _env_optional_float(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
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


def _env_optional_int(name: str) -> int | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError as exc:
        raise CialConfigError(f"{name} must be a positive integer") from exc
    if value <= 0:
        raise CialConfigError(f"{name} must be a positive integer")
    return value


def _load_active_profile() -> str:
    """
    Prefer CIAL_PROFILE. Legacy CIAL_PROVIDER / CIAL_DEFAULT_PROVIDER map to
    profiles for backward compatibility but are not the preferred surface.
    """
    explicit = os.environ.get("CIAL_PROFILE", "").strip().lower()
    if explicit:
        if explicit not in BUILTIN_PROFILE_IDS:
            raise CialConfigError(
                "CIAL_PROFILE must be one of: " + ", ".join(sorted(BUILTIN_PROFILE_IDS))
            )
        return explicit

    legacy = (
        os.environ.get("CIAL_PROVIDER", "").strip()
        or os.environ.get("CIAL_DEFAULT_PROVIDER", "").strip()
    )
    if legacy:
        if legacy.lower() not in {"mock", "openai"}:
            raise CialConfigError("legacy CIAL_PROVIDER must be mock|openai; prefer CIAL_PROFILE")
        return legacy_provider_to_profile(legacy)

    return PROFILE_DEFAULT


def load_cial_config() -> CialConfig:
    """
    Load CIAL settings.

    Safe defaults: profile=default (mock), live flag off, production never live.
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

    openai_model = os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL
    mock_model = os.environ.get("CIAL_DEFAULT_MODEL", "").strip() or DEFAULT_MODEL
    # If operator set CIAL_DEFAULT_MODEL while on research, treat it as openai model
    # only when OPENAI_MODEL unset — keep mock wire identity separate.
    if (
        os.environ.get("OPENAI_MODEL", "").strip() == ""
        and os.environ.get("CIAL_DEFAULT_MODEL", "").strip()
    ):
        # Prefer wire/mock identity for default/offline; research uses OPENAI_MODEL.
        pass

    app_env = (
        os.environ.get("APP_ENV", "").strip()
        or os.environ.get("COBRA_CORE_ENV", "").strip()
        or "staging"
    )

    return CialConfig(
        enabled=_env_bool("CIAL_ENABLED", True),
        active_profile=_load_active_profile(),
        routing_policy=policy,
        app_env=app_env,
        live_provider_enabled=_env_bool("CIAL_LIVE_PROVIDER_ENABLED", False),
        openai_base_url=(os.environ.get("OPENAI_BASE_URL", "").strip() or DEFAULT_OPENAI_BASE_URL),
        openai_api_key=os.environ.get("OPENAI_API_KEY", "").strip(),
        openai_model=openai_model,
        openai_timeout_seconds=_env_float("OPENAI_TIMEOUT_SECONDS", DEFAULT_OPENAI_TIMEOUT_SECONDS),
        openai_max_retries=_env_nonneg_int("OPENAI_MAX_RETRIES", DEFAULT_OPENAI_MAX_RETRIES),
        live_max_input_chars=_env_nonneg_int(
            "CIAL_LIVE_MAX_INPUT_CHARS", DEFAULT_LIVE_MAX_INPUT_CHARS
        )
        or DEFAULT_LIVE_MAX_INPUT_CHARS,
        live_max_output_tokens=_env_optional_int("CIAL_LIVE_MAX_OUTPUT_TOKENS"),
        live_max_concurrent=_env_nonneg_int("CIAL_LIVE_MAX_CONCURRENT", DEFAULT_LIVE_MAX_CONCURRENT)
        or DEFAULT_LIVE_MAX_CONCURRENT,
        live_daily_request_quota=_env_optional_int("CIAL_LIVE_DAILY_REQUEST_QUOTA"),
        live_daily_cost_ceiling=_env_optional_float("CIAL_LIVE_DAILY_COST_CEILING"),
        mock_model=mock_model,
    )
