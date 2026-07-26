"""RRF configuration (env + optional YAML). Invalid config fails closed."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _bool(raw: str | None, default: bool) -> bool:
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() not in {"0", "false", "no", "off"}


def _int(
    name: str, raw: str | None, default: int, *, min_v: int = 0, max_v: int = 10_000_000
) -> int:
    if raw is None or not str(raw).strip():
        return default
    try:
        value = int(str(raw).strip())
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {raw!r}") from exc
    if value < min_v or value > max_v:
        raise ValueError(f"{name} out of range [{min_v}, {max_v}]: {value}")
    return value


def _float(
    name: str, raw: str | None, default: float, *, min_v: float = 0.0, max_v: float = 1e6
) -> float:
    if raw is None or not str(raw).strip():
        return default
    try:
        value = float(str(raw).strip())
    except ValueError as exc:
        raise ValueError(f"invalid {name}: {raw!r}") from exc
    if value < min_v or value > max_v:
        raise ValueError(f"{name} out of range [{min_v}, {max_v}]: {value}")
    return value


@dataclass(frozen=True)
class ResilienceConfig:
    enabled: bool = True
    max_attempts: int = 2  # initial + 1 retry
    max_provider_calls: int = 3  # transport + repair ceiling
    max_repair_attempts: int = 1
    initial_backoff_ms: int = 250
    max_backoff_ms: int = 2000
    request_deadline_ms: int = 30_000
    provider_timeout_ms: int = 15_000
    circuit_failure_threshold: int = 5
    circuit_window_seconds: int = 60
    circuit_open_seconds: int = 30
    circuit_half_open_probes: int = 1
    circuit_success_threshold: int = 2
    allow_fallback: bool = True
    max_estimated_cost_usd: float = 0.50
    max_input_tokens: int = 8000
    max_output_tokens: int = 2048
    hourly_budget_usd: float = 5.0
    daily_budget_usd: float = 25.0
    policy_path: str = ""
    # Deterministic jitter seed (None = random); tests inject 0 for stability.
    jitter_seed: int | None = None

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.max_provider_calls < 1:
            raise ValueError("max_provider_calls must be >= 1")
        if self.max_repair_attempts < 0 or self.max_repair_attempts > 1:
            raise ValueError("max_repair_attempts must be 0 or 1")
        if self.initial_backoff_ms > self.max_backoff_ms:
            raise ValueError("initial_backoff_ms cannot exceed max_backoff_ms")
        if self.request_deadline_ms < 100:
            raise ValueError("request_deadline_ms too small")


def load_resilience_config(*, env: dict[str, str] | None = None) -> ResilienceConfig:
    e = env if env is not None else os.environ
    policy_path = (e.get("RRF_POLICY_PATH") or "").strip()
    file_overrides: dict[str, Any] = {}
    if policy_path:
        path = Path(policy_path)
        if not path.is_file():
            raise ValueError(f"RRF_POLICY_PATH not found: {policy_path}")
        import yaml  # local import — PyYAML already a Core dependency

        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError("RRF policy file must be a mapping")
        file_overrides = loaded

    def pick(key: str, env_key: str, default: Any) -> Any:
        if key in file_overrides:
            return file_overrides[key]
        return e.get(env_key)

    cfg = ResilienceConfig(
        enabled=_bool(pick("enabled", "RRF_ENABLED", None), True),
        max_attempts=_int(
            "RRF_MAX_ATTEMPTS", pick("max_attempts", "RRF_MAX_ATTEMPTS", None), 2, min_v=1, max_v=5
        ),
        max_provider_calls=_int(
            "RRF_MAX_PROVIDER_CALLS",
            pick("max_provider_calls", "RRF_MAX_PROVIDER_CALLS", None),
            3,
            min_v=1,
            max_v=10,
        ),
        initial_backoff_ms=_int(
            "RRF_INITIAL_BACKOFF_MS",
            pick("initial_backoff_ms", "RRF_INITIAL_BACKOFF_MS", None),
            250,
            min_v=0,
            max_v=60_000,
        ),
        max_backoff_ms=_int(
            "RRF_MAX_BACKOFF_MS",
            pick("max_backoff_ms", "RRF_MAX_BACKOFF_MS", None),
            2000,
            min_v=0,
            max_v=120_000,
        ),
        request_deadline_ms=_int(
            "RRF_REQUEST_DEADLINE_MS",
            pick("request_deadline_ms", "RRF_REQUEST_DEADLINE_MS", None),
            30_000,
            min_v=100,
            max_v=600_000,
        ),
        provider_timeout_ms=_int(
            "RRF_PROVIDER_TIMEOUT_MS",
            pick("provider_timeout_ms", "RRF_PROVIDER_TIMEOUT_MS", None),
            15_000,
            min_v=50,
            max_v=300_000,
        ),
        circuit_failure_threshold=_int(
            "RRF_CIRCUIT_FAILURE_THRESHOLD",
            pick("circuit_failure_threshold", "RRF_CIRCUIT_FAILURE_THRESHOLD", None),
            5,
            min_v=1,
            max_v=100,
        ),
        circuit_window_seconds=_int(
            "RRF_CIRCUIT_WINDOW_SECONDS",
            pick("circuit_window_seconds", "RRF_CIRCUIT_WINDOW_SECONDS", None),
            60,
            min_v=1,
            max_v=3600,
        ),
        circuit_open_seconds=_int(
            "RRF_CIRCUIT_OPEN_SECONDS",
            pick("circuit_open_seconds", "RRF_CIRCUIT_OPEN_SECONDS", None),
            30,
            min_v=1,
            max_v=3600,
        ),
        allow_fallback=_bool(pick("allow_fallback", "RRF_ALLOW_FALLBACK", None), True),
        max_estimated_cost_usd=_float(
            "RRF_MAX_ESTIMATED_COST_USD",
            pick("max_estimated_cost_usd", "RRF_MAX_ESTIMATED_COST_USD", None),
            0.50,
        ),
        max_input_tokens=_int(
            "RRF_MAX_INPUT_TOKENS",
            pick("max_input_tokens", "RRF_MAX_INPUT_TOKENS", None),
            8000,
            min_v=1,
        ),
        max_output_tokens=_int(
            "RRF_MAX_OUTPUT_TOKENS",
            pick("max_output_tokens", "RRF_MAX_OUTPUT_TOKENS", None),
            2048,
            min_v=1,
        ),
        hourly_budget_usd=_float(
            "RRF_HOURLY_BUDGET_USD",
            pick("hourly_budget_usd", "RRF_HOURLY_BUDGET_USD", None),
            5.0,
        ),
        daily_budget_usd=_float(
            "RRF_DAILY_BUDGET_USD",
            pick("daily_budget_usd", "RRF_DAILY_BUDGET_USD", None),
            25.0,
        ),
        policy_path=policy_path,
    )
    jitter_raw = pick("jitter_seed", "RRF_JITTER_SEED", None)
    if jitter_raw is not None and str(jitter_raw).strip() != "":
        object.__setattr__(
            cfg,
            "jitter_seed",
            _int("RRF_JITTER_SEED", str(jitter_raw), 0, min_v=0, max_v=2_147_483_647),
        )
    return cfg


def rrf_enabled() -> bool:
    return _bool(os.environ.get("RRF_ENABLED"), True)
