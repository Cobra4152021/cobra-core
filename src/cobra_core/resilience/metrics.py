"""RRF observability (bounded labels only)."""

from __future__ import annotations

import threading
from collections import Counter
from typing import Any

_ALLOWED_PROVIDERS = frozenset({"mock", "openai", "unknown", "none"})
_ALLOWED_MODELS = frozenset({"cobra-core-qwen3-8b", "gpt-5.4-mini", "unknown", "none"})
_ALLOWED_FAILURES = frozenset(
    {
        "authentication_failure",
        "authorization_failure",
        "rate_limited",
        "provider_timeout",
        "provider_unavailable",
        "provider_overloaded",
        "connection_failure",
        "invalid_provider_response",
        "structured_output_invalid",
        "schema_repair_failed",
        "capability_unavailable",
        "provider_unhealthy",
        "budget_exceeded",
        "request_deadline_exceeded",
        "circuit_open",
        "operator_disabled",
        "policy_blocked",
        "internal_execution_error",
        "cancelled",
        "none",
        "other",
    }
)
_ALLOWED_CIRCUIT = frozenset({"closed", "open", "half_open", "unknown"})
_ALLOWED_RESULT = frozenset(
    {"success", "failed", "cancelled", "budget_exceeded", "circuit_open", "other"}
)
_ALLOWED_SKILLS = frozenset(
    {
        "vehicle_damage_assessment",
        "policy_compliance_review",
        "contract_analysis",
        "budget_analysis",
        "evidence_summary",
        "timeline_construction",
        "pattern_detection",
        "open_source_research",
        "interview_summary",
        "document_comparison",
        "unknown",
    }
)


def _bound(value: str, allowed: frozenset[str], default: str) -> str:
    key = (value or default).strip().lower()
    return key if key in allowed else default


class ResilienceMetrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.execution_total = 0
        self.execution_success = 0
        self.execution_failure = 0
        self.provider_attempt_total = 0
        self.retry_total = 0
        self.retry_exhausted_total = 0
        self.backoff_seconds_sum = 0.0
        self.circuit_open_total = 0
        self.circuit_transition_total = 0
        self.fallback_attempt_total = 0
        self.fallback_success_total = 0
        self.fallback_failure_total = 0
        self.timeout_total = 0
        self.budget_exceeded_total = 0
        self.cancelled_total = 0
        self.idempotency_hit_total = 0
        self.latency_ms_sum = 0
        self.latency_ms_count = 0
        self.provider_latency_ms_sum = 0
        self.provider_latency_ms_count = 0
        self.by_provider: Counter[str] = Counter()
        self.by_failure: Counter[str] = Counter()
        self.by_result: Counter[str] = Counter()
        self.by_skill: Counter[str] = Counter()
        self.by_circuit: Counter[str] = Counter()

    def record_execution(
        self,
        *,
        skill_id: str,
        provider_id: str,
        result: str,
        failure_category: str | None,
        success: bool,
        retries: int = 0,
        retry_exhausted: bool = False,
        backoff_ms: int = 0,
        fallback_attempted: bool = False,
        fallback_success: bool = False,
        timeout: bool = False,
        budget_exceeded: bool = False,
        cancelled: bool = False,
        idempotency_hit: bool = False,
        latency_ms: int = 0,
        provider_attempts: int = 0,
        provider_latency_ms: int = 0,
        circuit_state: str = "closed",
    ) -> None:
        with self._lock:
            self.execution_total += 1
            if success:
                self.execution_success += 1
            else:
                self.execution_failure += 1
            self.provider_attempt_total += max(0, provider_attempts)
            self.retry_total += max(0, retries)
            if retry_exhausted:
                self.retry_exhausted_total += 1
            self.backoff_seconds_sum += max(0, backoff_ms) / 1000.0
            if fallback_attempted:
                self.fallback_attempt_total += 1
                if fallback_success:
                    self.fallback_success_total += 1
                else:
                    self.fallback_failure_total += 1
            if timeout:
                self.timeout_total += 1
            if budget_exceeded:
                self.budget_exceeded_total += 1
            if cancelled:
                self.cancelled_total += 1
            if idempotency_hit:
                self.idempotency_hit_total += 1
            self.latency_ms_sum += max(0, latency_ms)
            self.latency_ms_count += 1
            self.provider_latency_ms_sum += max(0, provider_latency_ms)
            if provider_attempts:
                self.provider_latency_ms_count += 1
            self.by_provider[_bound(provider_id, _ALLOWED_PROVIDERS, "unknown")] += 1
            self.by_result[_bound(result, _ALLOWED_RESULT, "other")] += 1
            self.by_skill[_bound(skill_id, _ALLOWED_SKILLS, "unknown")] += 1
            self.by_circuit[_bound(circuit_state, _ALLOWED_CIRCUIT, "unknown")] += 1
            if failure_category:
                self.by_failure[_bound(failure_category, _ALLOWED_FAILURES, "other")] += 1

    def record_circuit_transition(self) -> None:
        with self._lock:
            self.circuit_transition_total += 1

    def record_circuit_open(self) -> None:
        with self._lock:
            self.circuit_open_total += 1

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            avg = self.latency_ms_sum / self.latency_ms_count if self.latency_ms_count else 0.0
            return {
                "execution_total": self.execution_total,
                "execution_success": self.execution_success,
                "execution_failure": self.execution_failure,
                "provider_attempt_total": self.provider_attempt_total,
                "retry_total": self.retry_total,
                "retry_exhausted_total": self.retry_exhausted_total,
                "backoff_seconds": round(self.backoff_seconds_sum, 3),
                "circuit_open_total": self.circuit_open_total,
                "circuit_transition_total": self.circuit_transition_total,
                "fallback_attempt_total": self.fallback_attempt_total,
                "fallback_success_total": self.fallback_success_total,
                "fallback_failure_total": self.fallback_failure_total,
                "timeout_total": self.timeout_total,
                "budget_exceeded_total": self.budget_exceeded_total,
                "cancelled_total": self.cancelled_total,
                "idempotency_hit_total": self.idempotency_hit_total,
                "latency_ms_avg": round(avg, 3),
                "by_provider": dict(self.by_provider),
                "by_failure": dict(self.by_failure),
                "by_result": dict(self.by_result),
                "by_skill": dict(self.by_skill),
            }

    def render_prometheus(self) -> str:
        with self._lock:
            lines = [
                "# HELP rrf_execution_total RRF logical executions",
                "# TYPE rrf_execution_total counter",
                f"rrf_execution_total {self.execution_total}",
                "# HELP rrf_execution_success_total Successful RRF executions",
                "# TYPE rrf_execution_success_total counter",
                f"rrf_execution_success_total {self.execution_success}",
                "# HELP rrf_execution_failure_total Failed RRF executions",
                "# TYPE rrf_execution_failure_total counter",
                f"rrf_execution_failure_total {self.execution_failure}",
                "# HELP rrf_provider_attempt_total Provider attempts",
                "# TYPE rrf_provider_attempt_total counter",
                f"rrf_provider_attempt_total {self.provider_attempt_total}",
                "# HELP rrf_retry_total Retries",
                "# TYPE rrf_retry_total counter",
                f"rrf_retry_total {self.retry_total}",
                "# HELP rrf_retry_exhausted_total Retry exhaustions",
                "# TYPE rrf_retry_exhausted_total counter",
                f"rrf_retry_exhausted_total {self.retry_exhausted_total}",
                "# HELP rrf_backoff_seconds Backoff sleep seconds",
                "# TYPE rrf_backoff_seconds counter",
                f"rrf_backoff_seconds {self.backoff_seconds_sum}",
                "# HELP rrf_circuit_open_total Circuit opens",
                "# TYPE rrf_circuit_open_total counter",
                f"rrf_circuit_open_total {self.circuit_open_total}",
                "# HELP rrf_circuit_transition_total Circuit transitions",
                "# TYPE rrf_circuit_transition_total counter",
                f"rrf_circuit_transition_total {self.circuit_transition_total}",
                "# HELP rrf_fallback_attempt_total Fallback attempts",
                "# TYPE rrf_fallback_attempt_total counter",
                f"rrf_fallback_attempt_total {self.fallback_attempt_total}",
                "# HELP rrf_fallback_success_total Fallback successes",
                "# TYPE rrf_fallback_success_total counter",
                f"rrf_fallback_success_total {self.fallback_success_total}",
                "# HELP rrf_fallback_failure_total Fallback failures",
                "# TYPE rrf_fallback_failure_total counter",
                f"rrf_fallback_failure_total {self.fallback_failure_total}",
                "# HELP rrf_timeout_total Timeouts",
                "# TYPE rrf_timeout_total counter",
                f"rrf_timeout_total {self.timeout_total}",
                "# HELP rrf_budget_exceeded_total Budget denials",
                "# TYPE rrf_budget_exceeded_total counter",
                f"rrf_budget_exceeded_total {self.budget_exceeded_total}",
                "# HELP rrf_cancelled_total Cancellations",
                "# TYPE rrf_cancelled_total counter",
                f"rrf_cancelled_total {self.cancelled_total}",
                "# HELP rrf_idempotency_hit_total Idempotency hits",
                "# TYPE rrf_idempotency_hit_total counter",
                f"rrf_idempotency_hit_total {self.idempotency_hit_total}",
                "# HELP rrf_execution_latency_ms Execution latency",
                "# TYPE rrf_execution_latency_ms summary",
                f"rrf_execution_latency_ms_sum {self.latency_ms_sum}",
                f"rrf_execution_latency_ms_count {self.latency_ms_count}",
                "# HELP rrf_provider_latency_ms Provider latency",
                "# TYPE rrf_provider_latency_ms summary",
                f"rrf_provider_latency_ms_sum {self.provider_latency_ms_sum}",
                f"rrf_provider_latency_ms_count {self.provider_latency_ms_count}",
            ]
            return "\n".join(lines) + "\n"

    def reset(self) -> None:
        with self._lock:
            self.execution_total = 0
            self.execution_success = 0
            self.execution_failure = 0
            self.provider_attempt_total = 0
            self.retry_total = 0
            self.retry_exhausted_total = 0
            self.backoff_seconds_sum = 0.0
            self.circuit_open_total = 0
            self.circuit_transition_total = 0
            self.fallback_attempt_total = 0
            self.fallback_success_total = 0
            self.fallback_failure_total = 0
            self.timeout_total = 0
            self.budget_exceeded_total = 0
            self.cancelled_total = 0
            self.idempotency_hit_total = 0
            self.latency_ms_sum = 0
            self.latency_ms_count = 0
            self.provider_latency_ms_sum = 0
            self.provider_latency_ms_count = 0
            self.by_provider.clear()
            self.by_failure.clear()
            self.by_result.clear()
            self.by_skill.clear()
            self.by_circuit.clear()


RRF_METRICS = ResilienceMetrics()
