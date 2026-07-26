"""Provider/model circuit breakers (in-process; auditable transitions)."""

from __future__ import annotations

import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field

from cobra_core.resilience.config import ResilienceConfig
from cobra_core.resilience.types import CircuitState


@dataclass
class CircuitBreaker:
    key: str
    cfg: ResilienceConfig
    state: CircuitState = CircuitState.CLOSED
    opened_at: float = 0.0
    half_open_successes: int = 0
    half_open_probes: int = 0
    failures: deque[float] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)
    on_transition: Callable[[str, CircuitState, CircuitState], None] | None = None

    def _prune(self, now: float) -> None:
        window = float(self.cfg.circuit_window_seconds)
        while self.failures and now - self.failures[0] > window:
            self.failures.popleft()

    def _transition_unlocked(self, new_state: CircuitState) -> None:
        old = self.state
        if old == new_state:
            return
        self.state = new_state
        if new_state == CircuitState.OPEN:
            self.opened_at = time.monotonic()
            self.half_open_successes = 0
            self.half_open_probes = 0
        if new_state == CircuitState.CLOSED:
            self.failures.clear()
            self.half_open_successes = 0
            self.half_open_probes = 0
        if self.on_transition:
            self.on_transition(self.key, old, new_state)

    def _refresh_unlocked(self, now: float) -> CircuitState:
        if self.state == CircuitState.OPEN and now - self.opened_at >= float(
            self.cfg.circuit_open_seconds
        ):
            self._transition_unlocked(CircuitState.HALF_OPEN)
        return self.state

    def current_state(self, *, now: float | None = None) -> CircuitState:
        with self._lock:
            t = now if now is not None else time.monotonic()
            return self._refresh_unlocked(t)

    def allow_request(self) -> tuple[bool, CircuitState]:
        with self._lock:
            state = self._refresh_unlocked(time.monotonic())
            if state == CircuitState.CLOSED:
                return True, state
            if state == CircuitState.OPEN:
                return False, state
            # half-open: limited probes
            if self.half_open_probes >= self.cfg.circuit_half_open_probes:
                return False, state
            self.half_open_probes += 1
            return True, state

    def record_success(self) -> CircuitState:
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_successes += 1
                if self.half_open_successes >= self.cfg.circuit_success_threshold:
                    self._transition_unlocked(CircuitState.CLOSED)
            return self.state

    def record_failure(self) -> CircuitState:
        with self._lock:
            now = time.monotonic()
            if self.state == CircuitState.HALF_OPEN:
                self._transition_unlocked(CircuitState.OPEN)
                return self.state
            self._prune(now)
            self.failures.append(now)
            if len(self.failures) >= self.cfg.circuit_failure_threshold:
                self._transition_unlocked(CircuitState.OPEN)
            return self.state


class CircuitBreakerRegistry:
    def __init__(
        self,
        cfg: ResilienceConfig,
        *,
        on_transition: Callable[[str, CircuitState, CircuitState], None] | None = None,
    ) -> None:
        self.cfg = cfg
        self.on_transition = on_transition
        self._lock = threading.Lock()
        self._breakers: dict[str, CircuitBreaker] = {}

    def _key(self, provider_id: str, model_id: str) -> str:
        return f"{provider_id.strip().lower()}::{model_id.strip()}"

    def get(self, provider_id: str, model_id: str) -> CircuitBreaker:
        key = self._key(provider_id, model_id)
        with self._lock:
            br = self._breakers.get(key)
            if br is None:
                br = CircuitBreaker(key=key, cfg=self.cfg, on_transition=self.on_transition)
                self._breakers[key] = br
            return br

    def reset(self) -> None:
        with self._lock:
            self._breakers.clear()
