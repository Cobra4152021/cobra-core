"""Provider execution health (circuit + outcomes; probe cannot override open circuit)."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from cobra_core.resilience.circuit_breaker import CircuitBreakerRegistry
from cobra_core.resilience.types import CircuitState, ProviderHealthState


@dataclass
class HealthSnapshot:
    provider_id: str
    model_id: str
    state: ProviderHealthState
    circuit_state: CircuitState
    recent_successes: int = 0
    recent_failures: int = 0
    operator_disabled: bool = False


@dataclass
class HealthTracker:
    circuits: CircuitBreakerRegistry
    _outcomes: dict[str, list[bool]] = field(default_factory=dict)
    _operator: dict[str, bool] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def set_operator_disabled(self, provider_id: str, disabled: bool) -> None:
        with self._lock:
            self._operator[provider_id.strip().lower()] = disabled

    def record_outcome(self, provider_id: str, model_id: str, *, success: bool) -> None:
        key = f"{provider_id}::{model_id}"
        with self._lock:
            buf = self._outcomes.setdefault(key, [])
            buf.append(success)
            if len(buf) > 50:
                del buf[: len(buf) - 50]

    def snapshot(self, provider_id: str, model_id: str) -> HealthSnapshot:
        br = self.circuits.get(provider_id, model_id)
        circuit = br.current_state()
        with self._lock:
            op_disabled = bool(self._operator.get(provider_id.strip().lower(), False))
            outcomes = list(self._outcomes.get(f"{provider_id}::{model_id}", []))
        # Open circuit wins over optimistic probe.
        if circuit == CircuitState.OPEN or op_disabled:
            state = ProviderHealthState.UNAVAILABLE
        elif circuit == CircuitState.HALF_OPEN:
            state = ProviderHealthState.DEGRADED
        elif outcomes:
            fails = sum(1 for o in outcomes[-10:] if not o)
            state = (
                ProviderHealthState.DEGRADED if fails >= 5 else ProviderHealthState.HEALTHY
            )
        else:
            state = ProviderHealthState.UNKNOWN
        return HealthSnapshot(
            provider_id=provider_id,
            model_id=model_id,
            state=state,
            circuit_state=circuit,
            recent_successes=sum(1 for o in outcomes if o),
            recent_failures=sum(1 for o in outcomes if not o),
            operator_disabled=op_disabled,
        )
