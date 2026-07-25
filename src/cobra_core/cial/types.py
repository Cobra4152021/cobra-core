"""Provider-neutral CIAL request/result/registry contracts."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from cobra_core.cial.capabilities import Capability
from cobra_core.cial.health import HealthState


class RoutingPolicy(str, Enum):
    """Deterministic routing policies (Phase 1; fallback execution is later)."""

    DEFAULT = "default"
    LOWEST_COST = "lowest_cost"
    LOWEST_LATENCY = "lowest_latency"
    HIGHEST_QUALITY = "highest_quality"
    REASONING = "reasoning"
    RESEARCH = "research"
    MANUAL = "manual"


class QualityTier(str, Enum):
    """Relative quality ranking for deterministic highest_quality routing."""

    LOW = "low"
    STANDARD = "standard"
    HIGH = "high"
    PREMIUM = "premium"


class LatencyTier(str, Enum):
    """Relative latency ranking for deterministic lowest_latency routing."""

    FAST = "fast"
    STANDARD = "standard"
    SLOW = "slow"


_QUALITY_RANK: dict[QualityTier, int] = {
    QualityTier.LOW: 0,
    QualityTier.STANDARD: 1,
    QualityTier.HIGH: 2,
    QualityTier.PREMIUM: 3,
}

_LATENCY_RANK: dict[LatencyTier, int] = {
    LatencyTier.FAST: 0,
    LatencyTier.STANDARD: 1,
    LatencyTier.SLOW: 2,
}


def quality_rank(tier: QualityTier | str) -> int:
    if isinstance(tier, str):
        tier = QualityTier(tier)
    return _QUALITY_RANK[tier]


def latency_rank(tier: LatencyTier | str) -> int:
    if isinstance(tier, str):
        tier = LatencyTier(tier)
    return _LATENCY_RANK[tier]


@dataclass(frozen=True)
class ModelRecord:
    """Registered model metadata for routing (no live pricing in Phase 1)."""

    provider_id: str
    model_id: str
    display_name: str
    enabled: bool
    capabilities: frozenset[Capability]
    context_window: int
    max_output_tokens: int
    supports_json: bool
    supports_tools: bool
    supports_vision: bool
    supports_streaming: bool
    quality_tier: QualityTier
    latency_tier: LatencyTier
    estimated_input_cost: float | None
    estimated_output_cost: float | None
    revision: str
    metadata: dict[str, Any] = field(default_factory=dict)
    health: HealthState = HealthState.HEALTHY

    @property
    def key(self) -> tuple[str, str]:
        return (self.provider_id, self.model_id)

    def has_capabilities(self, required: frozenset[Capability]) -> bool:
        return required.issubset(self.capabilities)


@dataclass(frozen=True)
class RoutingRequest:
    """Input contract for the deterministic router."""

    policy: RoutingPolicy = RoutingPolicy.DEFAULT
    required_capabilities: frozenset[Capability] = field(default_factory=frozenset)
    manual_provider_id: str | None = None
    manual_model_id: str | None = None
    preferred_model_id: str | None = None


@dataclass(frozen=True)
class RouteDecision:
    """Selected model plus structured route reason (safe to log)."""

    provider_id: str
    model_id: str
    policy: RoutingPolicy
    reason: str
    health_state: HealthState
    fallback_count: int = 0


@dataclass
class GenerateRequest:
    """Provider-neutral generation request (no SDK objects)."""

    messages: list[dict[str, Any]]
    max_tokens: int
    model_id: str
    cancel_event: threading.Event | None = None
    delay_ms: int = 0
    fail: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class InferenceResult:
    """
    Provider-neutral generation result.

    Observability fields are internal to Core/CIAL — never Protocol V1 wire fields.
    """

    content: str
    prompt_tokens: int
    completion_tokens: int
    inference_ms: int
    cial_provider_id: str = ""
    cial_model_id: str = ""
    cial_routing_policy: str = ""
    cial_route_reason: str = ""
    cial_latency_ms: int = 0
    cial_fallback_count: int = 0
    cial_health_state: str = ""
