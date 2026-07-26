"""RRF request/result contracts."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cobra_core.air.capabilities import AirCapability
from cobra_core.resilience.errors import FailureCategory


class CircuitState(StrEnum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class ProviderHealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class ExecutionStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BUDGET_EXCEEDED = "budget_exceeded"
    CIRCUIT_OPEN = "circuit_open"
    DEADLINE_EXCEEDED = "deadline_exceeded"


@dataclass(frozen=True)
class RouteTarget:
    provider_id: str
    model_id: str
    route_reason: str = ""
    capabilities: frozenset[AirCapability] = field(default_factory=frozenset)


@dataclass
class AttemptRecord:
    attempt_number: int
    provider_id: str
    model_id: str
    failure_category: FailureCategory | None = None
    retry_decision: str = ""
    backoff_ms: int = 0
    circuit_state_before: str = ""
    circuit_state_after: str = ""
    schema_repair_attempt: bool = False
    estimated_cost_usd: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: int = 0
    success: bool = False


@dataclass
class ResilienceRequest:
    """Logical provider execution (one ISF invocation)."""

    execution_id: str
    correlation_id: str
    skill_id: str
    skill_version: str
    profile_id: str
    required_capabilities: frozenset[AirCapability]
    primary: RouteTarget
    allow_offline_fallback: bool = False
    allow_live_fallback: bool = False
    revision: str = "1"
    estimated_input_tokens: int = 256
    max_output_tokens: int = 1024
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResilienceResult:
    status: ExecutionStatus
    content: str = ""
    provider_id: str = ""
    model_id: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    attempts: list[AttemptRecord] = field(default_factory=list)
    failure_category: FailureCategory | None = None
    schema_repair_count: int = 0
    fallback_used: bool = False
    total_estimated_cost_usd: float = 0.0
    execution_id: str = ""
    idempotency_hit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# Callable that performs a single provider generate (no AIR re-route).
ProviderCall = Callable[..., Any]
