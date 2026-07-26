"""Typed contracts for the Operations Control Plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ComponentHealth(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class QuotaTier(StrEnum):
    OK = "ok"
    WARNING = "warning"
    SOFT_LIMIT = "soft_limit"
    HARD_LIMIT = "hard_limit"


class AlertSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class ComponentHealthReport:
    component: str
    status: ComponentHealth
    detail: str = ""
    checked_at: float = 0.0


@dataclass(frozen=True)
class FeatureFlag:
    name: str
    enabled: bool
    version: int
    description: str = ""
    updated_at: float = 0.0
    updated_by: str = "system"


@dataclass(frozen=True)
class QuotaLimit:
    name: str
    warning: int
    soft_limit: int
    hard_limit: int


@dataclass(frozen=True)
class QuotaUsage:
    name: str
    used: int
    warning: int
    soft_limit: int
    hard_limit: int
    tier: QuotaTier


@dataclass(frozen=True)
class UsageSnapshot:
    active_users: int = 0
    active_cases: int = 0
    active_workflows: int = 0
    provider_utilization: float = 0.0
    average_latency_ms: float = 0.0
    estimated_cost_usd: float = 0.0
    storage_growth_bytes: int = 0
    day_key: str = ""
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperationalAlert:
    alert_id: str
    code: str
    severity: AlertSeverity
    message: str
    component: str = ""
    created_at: float = 0.0
    informational_only: bool = True


@dataclass(frozen=True)
class MaintenanceState:
    active: bool
    entered_at: float | None = None
    entered_by: str = ""
    reason: str = ""
    drain_workflows: bool = True
    reject_new_workflows: bool = True
    metrics_enabled: bool = True
    audit_enabled: bool = True
    reporting_enabled: bool = True
