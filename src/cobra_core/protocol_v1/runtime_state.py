"""Inference readiness state (separate from HTTP transport)."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RuntimeState:
    """Tracks whether the model runtime is loaded and ready for generation."""

    inference_mode: str
    model_loaded: bool = False
    load_error: str | None = None
    generation_calls: int = 0
    _lock: Lock = field(default_factory=Lock, repr=False)

    def mark_loaded(self) -> None:
        with self._lock:
            self.model_loaded = True
            self.load_error = None

    def mark_load_failed(self, safe_reason: str) -> None:
        with self._lock:
            self.model_loaded = False
            self.load_error = safe_reason

    def record_generation(self) -> None:
        with self._lock:
            self.generation_calls += 1

    @property
    def inference_ready(self) -> bool:
        """True only when generation can run without claiming a false model load."""
        if self.inference_mode in {"mock", "echo", "test"}:
            return True
        return self.model_loaded

    def health_reason(self) -> str:
        if self.inference_mode in {"mock", "echo", "test"}:
            return "ok"
        if self.model_loaded:
            return "ok"
        if self.load_error:
            return "model_unavailable"
        return "model_not_loaded"
