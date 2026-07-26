"""Operations Control Plane configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(raw: str | None, default: int) -> int:
    if raw is None or not str(raw).strip():
        return default
    return int(raw)


@dataclass(frozen=True)
class OperationsConfig:
    enabled: bool = True
    # Default daily quotas (0 = unlimited / tracking only).
    quota_cases_per_day: int = 1000
    quota_workflows_per_day: int = 5000
    quota_provider_calls_per_day: int = 10000
    quota_vault_retrievals_per_day: int = 20000
    quota_benchmark_runs_per_day: int = 500
    # Soft = 90% of hard, warning = 75% of hard (computed in Quotas).
    warning_ratio: float = 0.75
    soft_ratio: float = 0.90

    def __post_init__(self) -> None:
        if not 0.0 < self.warning_ratio <= self.soft_ratio <= 1.0:
            raise ValueError("invalid warning/soft ratios")


def load_operations_config(env: dict[str, str] | None = None) -> OperationsConfig:
    e = env if env is not None else os.environ
    return OperationsConfig(
        enabled=_bool(e.get("OCP_ENABLED"), True),
        quota_cases_per_day=_int(e.get("OCP_QUOTA_CASES_DAY"), 1000),
        quota_workflows_per_day=_int(e.get("OCP_QUOTA_WORKFLOWS_DAY"), 5000),
        quota_provider_calls_per_day=_int(e.get("OCP_QUOTA_PROVIDER_DAY"), 10000),
        quota_vault_retrievals_per_day=_int(e.get("OCP_QUOTA_VAULT_DAY"), 20000),
        quota_benchmark_runs_per_day=_int(e.get("OCP_QUOTA_BENCHMARK_DAY"), 500),
    )
