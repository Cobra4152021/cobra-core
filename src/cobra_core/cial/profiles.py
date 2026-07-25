"""
Named inference profiles for CIAL / AIR.

Profiles describe requirements (capabilities, live need). They do not
hardcode providers or models — AIR selects those at route time.

Compatibility: ``provider_id`` / ``model_id`` remain on InferenceProfile as
*preview bindings* for config introspection when AIR is unavailable; the
engine prefers AIR decisions for all generation.
"""

from __future__ import annotations

from dataclasses import dataclass

from cobra_core.protocol_v1.constants import DEFAULT_MODEL

PROFILE_DEFAULT = "default"
PROFILE_OFFLINE = "offline"
PROFILE_RESEARCH = "research"
PROFILE_ANALYSIS = "analysis"
PROFILE_CODING = "coding"

BUILTIN_PROFILE_IDS = frozenset(
    {
        PROFILE_DEFAULT,
        PROFILE_OFFLINE,
        PROFILE_RESEARCH,
        PROFILE_ANALYSIS,
        PROFILE_CODING,
    }
)


@dataclass(frozen=True)
class InferenceProfile:
    """
    Named profile → routing requirements.

    ``provider_id`` / ``model_id`` are legacy preview fields (offline → mock,
    research → openai when operators enable live). Runtime selection is AIR.
    """

    profile_id: str
    requires_live: bool
    description: str
    required_capabilities: frozenset[str]
    budget: str = "normal"
    latency: str = "normal"
    # Legacy preview bindings for config/diagnostics (not Computer activation).
    provider_id: str = "mock"
    model_id: str = DEFAULT_MODEL


def resolve_profile(
    profile_id: str,
    *,
    openai_model: str,
    mock_model: str = DEFAULT_MODEL,
) -> InferenceProfile:
    """Map a named profile to requirements (+ legacy preview binding)."""
    key = (profile_id or PROFILE_DEFAULT).strip().lower()
    if key == PROFILE_RESEARCH:
        return InferenceProfile(
            profile_id=PROFILE_RESEARCH,
            requires_live=True,
            description="Investigation / research — AIR selects live when gate open",
            required_capabilities=frozenset(
                {"reasoning", "summarization", "structured_output", "research"}
            ),
            budget="normal",
            latency="normal",
            provider_id="openai",
            model_id=openai_model,
        )
    if key == PROFILE_OFFLINE:
        return InferenceProfile(
            profile_id=PROFILE_OFFLINE,
            requires_live=False,
            description="Explicit offline / mock-only requirements",
            required_capabilities=frozenset({"text", "offline"}),
            budget="low",
            latency="fast",
            provider_id="mock",
            model_id=mock_model,
        )
    if key == PROFILE_ANALYSIS:
        return InferenceProfile(
            profile_id=PROFILE_ANALYSIS,
            requires_live=False,
            description="Analysis / classification requirements",
            required_capabilities=frozenset(
                {"reasoning", "classification", "structured_output"}
            ),
            budget="normal",
            latency="normal",
            provider_id="mock",
            model_id=mock_model,
        )
    if key == PROFILE_CODING:
        return InferenceProfile(
            profile_id=PROFILE_CODING,
            requires_live=False,
            description="Coding assistance requirements",
            required_capabilities=frozenset({"coding", "reasoning"}),
            budget="normal",
            latency="normal",
            provider_id="mock",
            model_id=mock_model,
        )
    if key == PROFILE_DEFAULT:
        return InferenceProfile(
            profile_id=PROFILE_DEFAULT,
            requires_live=False,
            description="Safe default — offline-capable text (AIR selects mock)",
            required_capabilities=frozenset({"text", "offline"}),
            budget="low",
            latency="fast",
            provider_id="mock",
            model_id=mock_model,
        )
    raise ValueError(f"unknown CIAL profile: {profile_id!r}")


def legacy_provider_to_profile(provider: str) -> str:
    """Map deprecated CIAL_PROVIDER values to profiles (compat only)."""
    p = (provider or "").strip().lower()
    if p == "openai":
        return PROFILE_RESEARCH
    return PROFILE_DEFAULT
