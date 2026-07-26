"""Deterministic fault-injection transport for unit/staging tests (no real providers)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from cobra_core.cial.types import InferenceResult
from cobra_core.resilience.errors import FailureCategory, ResilienceError


@dataclass
class FaultScript:
    """Sequence of behaviors; each call consumes the next step."""

    steps: list[str] = field(default_factory=list)
    # Optional payloads for success steps (JSON string content).
    success_content: str = '{"summary":"ok","confidence":0.4,"missing_information":[],"recommended_next_steps":[],"needs_human_review":true,"themes":[],"evidence_count":1,"gaps":[]}'
    retry_after_ms: int = 100
    slow_ms: int = 50
    _idx: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def next_step(self) -> str:
        with self._lock:
            if self._idx >= len(self.steps):
                return "success"
            step = self.steps[self._idx]
            self._idx += 1
            return step


class FaultInjectingCaller:
    """
    Drop-in for ResilienceExecutor provider_call.

    Supported steps:
      timeout, connection_reset, http_401, http_403, http_429, http_500,
      http_502, http_503, malformed_json, empty, slow, success, cancel
    """

    def __init__(self, script: FaultScript) -> None:
        self.script = script
        self.calls: list[dict[str, Any]] = []

    def __call__(
        self,
        *,
        provider_id: str,
        model_id: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        cancel_event: threading.Event | None = None,
        timeout_ms: int = 15_000,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceResult:
        step = self.script.next_step()
        self.calls.append(
            {
                "provider_id": provider_id,
                "model_id": model_id,
                "step": step,
                "max_tokens": max_tokens,
                "repair": bool((metadata or {}).get("schema_repair")),
            }
        )
        if cancel_event is not None and cancel_event.is_set():
            raise ResilienceError(FailureCategory.CANCELLED)
        if step == "cancel":
            raise ResilienceError(FailureCategory.CANCELLED)
        if step == "timeout":
            raise ResilienceError(FailureCategory.PROVIDER_TIMEOUT)
        if step == "connection_reset":
            raise ResilienceError(FailureCategory.CONNECTION_FAILURE)
        if step == "http_401":
            raise ResilienceError(FailureCategory.AUTHENTICATION_FAILURE)
        if step == "http_403":
            raise ResilienceError(FailureCategory.AUTHORIZATION_FAILURE)
        if step == "http_429":
            raise ResilienceError(
                FailureCategory.RATE_LIMITED, retry_after_ms=self.script.retry_after_ms
            )
        if step == "http_500":
            raise ResilienceError(FailureCategory.PROVIDER_OVERLOADED)
        if step == "http_502":
            raise ResilienceError(FailureCategory.PROVIDER_OVERLOADED)
        if step == "http_503":
            raise ResilienceError(FailureCategory.PROVIDER_UNAVAILABLE)
        if step == "empty":
            return InferenceResult(
                content="",
                prompt_tokens=1,
                completion_tokens=0,
                inference_ms=1,
                cial_provider_id=provider_id,
                cial_model_id=model_id,
            )
        if step == "malformed_json":
            return InferenceResult(
                content="not-json{{{",
                prompt_tokens=10,
                completion_tokens=5,
                inference_ms=5,
                cial_provider_id=provider_id,
                cial_model_id=model_id,
            )
        if step == "slow":
            time.sleep(max(0, self.script.slow_ms) / 1000.0)
        # success (default)
        return InferenceResult(
            content=self.script.success_content,
            prompt_tokens=12,
            completion_tokens=20,
            inference_ms=max(1, self.script.slow_ms if step == "slow" else 5),
            cial_provider_id=provider_id,
            cial_model_id=model_id,
        )


def scripted_caller(steps: list[str], **kwargs: Any) -> FaultInjectingCaller:
    return FaultInjectingCaller(FaultScript(steps=steps, **kwargs))
