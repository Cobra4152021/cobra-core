"""
Named inference profiles for CIAL.

Deployments and Computer select a profile (default / offline / research).
CIAL resolves each profile to an internal provider + model. Vendors are not
part of the external activation surface.
"""

from __future__ import annotations

from dataclasses import dataclass

from cobra_core.protocol_v1.constants import DEFAULT_MODEL

PROFILE_DEFAULT = "default"
PROFILE_OFFLINE = "offline"
PROFILE_RESEARCH = "research"

BUILTIN_PROFILE_IDS = frozenset({PROFILE_DEFAULT, PROFILE_OFFLINE, PROFILE_RESEARCH})


@dataclass(frozen=True)
class InferenceProfile:
    """Resolved profile → internal provider/model binding."""

    profile_id: str
    provider_id: str
    model_id: str
    requires_live: bool
    description: str


def resolve_profile(
    profile_id: str,
    *,
    openai_model: str,
    mock_model: str = DEFAULT_MODEL,
) -> InferenceProfile:
    """Map a named profile to an internal provider/model pair."""
    key = (profile_id or PROFILE_DEFAULT).strip().lower()
    if key == PROFILE_RESEARCH:
        return InferenceProfile(
            profile_id=PROFILE_RESEARCH,
            provider_id="openai",
            model_id=openai_model,
            requires_live=True,
            description="Staging research profile (OpenAI-compatible when live-enabled)",
        )
    if key == PROFILE_OFFLINE:
        return InferenceProfile(
            profile_id=PROFILE_OFFLINE,
            provider_id="mock",
            model_id=mock_model,
            requires_live=False,
            description="Explicit offline / mock-only profile",
        )
    if key == PROFILE_DEFAULT:
        return InferenceProfile(
            profile_id=PROFILE_DEFAULT,
            provider_id="mock",
            model_id=mock_model,
            requires_live=False,
            description="Safe default mock profile (Internal Alpha)",
        )
    raise ValueError(f"unknown CIAL profile: {profile_id!r}")


def legacy_provider_to_profile(provider: str) -> str:
    """Map deprecated CIAL_PROVIDER values to profiles (compat only)."""
    p = (provider or "").strip().lower()
    if p == "openai":
        return PROFILE_RESEARCH
    return PROFILE_DEFAULT
