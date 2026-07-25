"""AIR request/decision contracts (safe to audit; never includes prompts)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cobra_core.air.capabilities import AirCapability
from cobra_core.cial.health import HealthState


class PriorityClass(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class BudgetClass(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class LatencyClass(StrEnum):
    FAST = "fast"
    NORMAL = "normal"
    SLOW = "slow"


class CostClass(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    UNKNOWN = "unknown"


_BUDGET_RANK = {BudgetClass.LOW: 0, BudgetClass.NORMAL: 1, BudgetClass.HIGH: 2}
_LATENCY_RANK = {LatencyClass.FAST: 0, LatencyClass.NORMAL: 1, LatencyClass.SLOW: 2}
_COST_RANK = {
    CostClass.LOW: 0,
    CostClass.NORMAL: 1,
    CostClass.HIGH: 2,
    CostClass.UNKNOWN: 3,
}
_HEALTH_RANK = {
    HealthState.HEALTHY: 0,
    HealthState.UNKNOWN: 1,
    HealthState.DEGRADED: 2,
}


def budget_rank(value: BudgetClass | str) -> int:
    if isinstance(value, str):
        value = BudgetClass(value)
    return _BUDGET_RANK[value]


def latency_class_rank(value: LatencyClass | str) -> int:
    if isinstance(value, str):
        value = LatencyClass(value)
    return _LATENCY_RANK[value]


def cost_class_rank(value: CostClass | str) -> int:
    if isinstance(value, str):
        value = CostClass(value)
    return _COST_RANK[value]


def health_rank(state: HealthState) -> int:
    return _HEALTH_RANK.get(state, 99)


@dataclass(frozen=True)
class AirRequest:
    """
    Capability request from Computer / Core (never provider or model ids).

    ``task`` is an opaque label for audit; routing uses capabilities + classes.
    """

    task: str = "general"
    capabilities: frozenset[AirCapability] = field(default_factory=frozenset)
    priority: PriorityClass = PriorityClass.NORMAL
    budget: BudgetClass = BudgetClass.NORMAL
    latency: LatencyClass = LatencyClass.NORMAL
    profile_id: str = "default"
    correlation_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AirDecision:
    """Single deterministic routing decision (auditable)."""

    profile_id: str
    requested_capabilities: frozenset[AirCapability]
    provider_id: str
    model_id: str
    reason: str
    health_state: HealthState
    estimated_cost_class: CostClass
    latency_class: LatencyClass
    timestamp_ms: int
    policy_id: str = "default_v1"
    task: str = "general"
    priority: PriorityClass = PriorityClass.NORMAL
    budget: BudgetClass = BudgetClass.NORMAL
    requested_latency: LatencyClass = LatencyClass.NORMAL
    correlation_id: str = ""


@dataclass(frozen=True)
class ModelDescriptor:
    """Provider-advertised model for AIR matching (registration surface)."""

    provider_id: str
    model_id: str
    capabilities: frozenset[AirCapability]
    estimated_cost: CostClass = CostClass.NORMAL
    latency: LatencyClass = LatencyClass.NORMAL
    health: HealthState = HealthState.HEALTHY
    enabled: bool = True
    requires_live: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> tuple[str, str]:
        return (self.provider_id, self.model_id)

    def has_capabilities(self, required: frozenset[AirCapability]) -> bool:
        return required.issubset(self.capabilities)


@dataclass(frozen=True)
class ProviderDescriptor:
    """Provider registration entry; models are listed separately or nested."""

    provider_id: str
    display_name: str
    models: tuple[ModelDescriptor, ...]
    enabled: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
