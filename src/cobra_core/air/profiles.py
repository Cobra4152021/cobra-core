"""
AIR policy profiles — requirements only (no provider/model hardcoding).

Computer selects a named profile; AIR resolves capabilities/budget/latency
and chooses a provider/model from the registry.
"""

from __future__ import annotations

from dataclasses import dataclass

from cobra_core.air.capabilities import AirCapability
from cobra_core.air.types import AirRequest, BudgetClass, LatencyClass, PriorityClass

PROFILE_DEFAULT = "default"
PROFILE_OFFLINE = "offline"
PROFILE_RESEARCH = "research"
PROFILE_ANALYSIS = "analysis"
PROFILE_CODING = "coding"

BUILTIN_AIR_PROFILE_IDS = frozenset(
    {
        PROFILE_DEFAULT,
        PROFILE_OFFLINE,
        PROFILE_RESEARCH,
        PROFILE_ANALYSIS,
        PROFILE_CODING,
    }
)


@dataclass(frozen=True)
class AirProfilePolicy:
    """Named profile → routing requirements (vendor-neutral)."""

    profile_id: str
    task: str
    required_capabilities: frozenset[AirCapability]
    priority: PriorityClass
    budget: BudgetClass
    latency: LatencyClass
    requires_live: bool
    allow_offline_fallback: bool
    description: str


def _caps(*values: AirCapability) -> frozenset[AirCapability]:
    return frozenset(values)


_BUILTIN: dict[str, AirProfilePolicy] = {
    PROFILE_DEFAULT: AirProfilePolicy(
        profile_id=PROFILE_DEFAULT,
        task="general",
        required_capabilities=_caps(AirCapability.TEXT, AirCapability.OFFLINE),
        priority=PriorityClass.NORMAL,
        budget=BudgetClass.LOW,
        latency=LatencyClass.FAST,
        requires_live=False,
        allow_offline_fallback=True,
        description="Safe default — offline-capable text",
    ),
    PROFILE_OFFLINE: AirProfilePolicy(
        profile_id=PROFILE_OFFLINE,
        task="offline",
        required_capabilities=_caps(AirCapability.TEXT, AirCapability.OFFLINE),
        priority=PriorityClass.NORMAL,
        budget=BudgetClass.LOW,
        latency=LatencyClass.FAST,
        requires_live=False,
        allow_offline_fallback=True,
        description="Explicit offline-only policy",
    ),
    PROFILE_RESEARCH: AirProfilePolicy(
        profile_id=PROFILE_RESEARCH,
        task="investigation",
        required_capabilities=_caps(
            AirCapability.REASONING,
            AirCapability.SUMMARIZATION,
            AirCapability.STRUCTURED_OUTPUT,
            AirCapability.RESEARCH,
        ),
        priority=PriorityClass.NORMAL,
        budget=BudgetClass.NORMAL,
        latency=LatencyClass.NORMAL,
        requires_live=True,
        allow_offline_fallback=True,  # when live gate closed → mock path (explicit)
        description="Investigation / research — prefers live when enabled",
    ),
    PROFILE_ANALYSIS: AirProfilePolicy(
        profile_id=PROFILE_ANALYSIS,
        task="analysis",
        required_capabilities=_caps(
            AirCapability.REASONING,
            AirCapability.CLASSIFICATION,
            AirCapability.STRUCTURED_OUTPUT,
        ),
        priority=PriorityClass.NORMAL,
        budget=BudgetClass.NORMAL,
        latency=LatencyClass.NORMAL,
        requires_live=False,
        allow_offline_fallback=True,
        description="Analysis / classification workloads",
    ),
    PROFILE_CODING: AirProfilePolicy(
        profile_id=PROFILE_CODING,
        task="coding",
        required_capabilities=_caps(AirCapability.CODING, AirCapability.REASONING),
        priority=PriorityClass.NORMAL,
        budget=BudgetClass.NORMAL,
        latency=LatencyClass.NORMAL,
        requires_live=False,
        allow_offline_fallback=True,
        description="Coding assistance policy",
    ),
}


def list_air_profiles() -> list[AirProfilePolicy]:
    return [_BUILTIN[k] for k in sorted(_BUILTIN)]


def get_air_profile(profile_id: str) -> AirProfilePolicy:
    key = (profile_id or PROFILE_DEFAULT).strip().lower()
    if key not in _BUILTIN:
        raise ValueError(f"unknown AIR profile: {profile_id!r}")
    return _BUILTIN[key]


def air_request_from_profile(
    profile_id: str,
    *,
    extra_capabilities: frozenset[AirCapability] | None = None,
    priority: PriorityClass | None = None,
    budget: BudgetClass | None = None,
    latency: LatencyClass | None = None,
    task: str | None = None,
) -> AirRequest:
    """Build an AirRequest from a named profile, optionally overriding classes."""
    policy = get_air_profile(profile_id)
    caps = set(policy.required_capabilities)
    if extra_capabilities:
        caps |= set(extra_capabilities)
    return AirRequest(
        task=task or policy.task,
        capabilities=frozenset(caps),
        priority=priority or policy.priority,
        budget=budget or policy.budget,
        latency=latency or policy.latency,
        profile_id=policy.profile_id,
        metadata={"requires_live": policy.requires_live},
    )


def air_request_from_contract(
    *,
    task: str = "general",
    capabilities: list[str] | frozenset[str] | None = None,
    priority: str = "normal",
    budget: str = "low",
    latency: str = "normal",
    profile_id: str = PROFILE_DEFAULT,
) -> AirRequest:
    """Parse the Computer-facing capability contract into an AirRequest."""
    from cobra_core.air.capabilities import parse_air_capabilities

    caps = parse_air_capabilities(capabilities or ())
    return AirRequest(
        task=task,
        capabilities=caps,
        priority=PriorityClass(priority.strip().lower()),
        budget=BudgetClass(budget.strip().lower()),
        latency=LatencyClass(latency.strip().lower()),
        profile_id=(profile_id or PROFILE_DEFAULT).strip().lower(),
    )
