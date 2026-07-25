"""
In-process metrics for Protocol V1 (RC1).

No prompts, responses, secrets, cookies, or JWTs are stored.
Prometheus text exposition is available via render_prometheus().
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field


@dataclass
class MetricsRegistry:
    requests_total: int = 0
    requests_success: int = 0
    requests_error: int = 0
    auth_failures: int = 0
    rate_limited: int = 0
    timeouts: int = 0
    cancellations: int = 0
    prompt_tokens_total: int = 0
    completion_tokens_total: int = 0
    latency_ms_sum: int = 0
    latency_ms_count: int = 0
    active_inflight: int = 0
    kill_switch_blocks: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def inc(self, name: str, *, n: int = 1) -> None:
        with self._lock:
            cur = getattr(self, name, None)
            if isinstance(cur, int):
                setattr(self, name, cur + n)

    def observe_latency(self, latency_ms: int) -> None:
        with self._lock:
            self.latency_ms_sum += max(0, latency_ms)
            self.latency_ms_count += 1

    def set_inflight(self, n: int) -> None:
        with self._lock:
            self.active_inflight = max(0, n)

    def snapshot(self) -> dict[str, int | float]:
        with self._lock:
            avg = (self.latency_ms_sum / self.latency_ms_count) if self.latency_ms_count else 0.0
            return {
                "requests_total": self.requests_total,
                "requests_success": self.requests_success,
                "requests_error": self.requests_error,
                "auth_failures": self.auth_failures,
                "rate_limited": self.rate_limited,
                "timeouts": self.timeouts,
                "cancellations": self.cancellations,
                "prompt_tokens_total": self.prompt_tokens_total,
                "completion_tokens_total": self.completion_tokens_total,
                "latency_ms_avg": round(avg, 3),
                "latency_ms_count": self.latency_ms_count,
                "active_inflight": self.active_inflight,
                "kill_switch_blocks": self.kill_switch_blocks,
            }

    def render_prometheus(self) -> str:
        s = self.snapshot()
        lines = [
            "# HELP cobra_core_requests_total Total completion requests seen",
            "# TYPE cobra_core_requests_total counter",
            f"cobra_core_requests_total {s['requests_total']}",
            "# HELP cobra_core_requests_success_total Successful completions",
            "# TYPE cobra_core_requests_success_total counter",
            f"cobra_core_requests_success_total {s['requests_success']}",
            "# HELP cobra_core_requests_error_total Failed completions",
            "# TYPE cobra_core_requests_error_total counter",
            f"cobra_core_requests_error_total {s['requests_error']}",
            "# HELP cobra_core_auth_failures_total Authentication failures",
            "# TYPE cobra_core_auth_failures_total counter",
            f"cobra_core_auth_failures_total {s['auth_failures']}",
            "# HELP cobra_core_rate_limited_total Admission/quota rejections",
            "# TYPE cobra_core_rate_limited_total counter",
            f"cobra_core_rate_limited_total {s['rate_limited']}",
            "# HELP cobra_core_timeouts_total Timeouts",
            "# TYPE cobra_core_timeouts_total counter",
            f"cobra_core_timeouts_total {s['timeouts']}",
            "# HELP cobra_core_active_inflight In-flight inferences",
            "# TYPE cobra_core_active_inflight gauge",
            f"cobra_core_active_inflight {s['active_inflight']}",
            "# HELP cobra_core_prompt_tokens_total Prompt tokens",
            "# TYPE cobra_core_prompt_tokens_total counter",
            f"cobra_core_prompt_tokens_total {s['prompt_tokens_total']}",
            "# HELP cobra_core_completion_tokens_total Completion tokens",
            "# TYPE cobra_core_completion_tokens_total counter",
            f"cobra_core_completion_tokens_total {s['completion_tokens_total']}",
            "# HELP cobra_core_kill_switch_blocks_total Kill-switch denials",
            "# TYPE cobra_core_kill_switch_blocks_total counter",
            f"cobra_core_kill_switch_blocks_total {s['kill_switch_blocks']}",
        ]
        # KC-023 — append AIR metrics (bounded labels; no prompts/ids).
        try:
            from cobra_core.air.metrics import AIR_METRICS

            air_text = AIR_METRICS.render_prometheus().rstrip("\n")
            if air_text:
                lines.append(air_text)
        except Exception:  # noqa: BLE001 — metrics must never break exposition
            pass
        return "\n".join(lines) + "\n"

    def reset_for_tests(self) -> None:
        with self._lock:
            self.requests_total = 0
            self.requests_success = 0
            self.requests_error = 0
            self.auth_failures = 0
            self.rate_limited = 0
            self.timeouts = 0
            self.cancellations = 0
            self.prompt_tokens_total = 0
            self.completion_tokens_total = 0
            self.latency_ms_sum = 0
            self.latency_ms_count = 0
            self.active_inflight = 0
            self.kill_switch_blocks = 0


# Process-wide default registry (tests may reset).
METRICS = MetricsRegistry()
