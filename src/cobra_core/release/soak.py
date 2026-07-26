"""
RC1 soak harness.

Full RC1 exit criteria require a 24-hour staging soak.
This module supports timed soaks for local/offline evidence and records
whether the mandatory 24h staging soak has been completed.
"""

from __future__ import annotations

import time
from typing import Any

from cobra_core.api.rate_limit import RATE_LIMITER
from cobra_core.api.router import API_GATEWAY, ApiRequest
from cobra_core.production.performance import PERFORMANCE


def run_timed_soak(
    *,
    duration_s: float = 60.0,
    interval_s: float = 0.25,
    label: str = "local_soak",
) -> dict[str, Any]:
    """Run a bounded in-process soak (not a substitute for 24h staging)."""
    RATE_LIMITER.reset_for_tests()
    RATE_LIMITER.org_limit = 1_000_000
    RATE_LIMITER.client_limit = 1_000_000

    t0 = time.perf_counter()
    deadline = t0 + max(1.0, duration_s)
    latencies: list[float] = []
    errors = 0
    requests = 0
    mem_samples: list[float] = []

    while time.perf_counter() < deadline:
        i = requests
        st = time.perf_counter()
        resp = API_GATEWAY.dispatch(
            ApiRequest(
                method="GET",
                path="/api/v1/status",
                request_id=f"soak_{label}_{i}",
                authenticated=True,
                principal_id="sys_cobra",
                organization_id="_system",
                api_client_id="client_soak",
                identity_verified=True,
            )
        )
        ms = (time.perf_counter() - st) * 1000
        latencies.append(ms)
        requests += 1
        if resp.status != 200:
            errors += 1
        snap = PERFORMANCE.sample(api_latency_ms=ms, request_latency_ms=ms)
        if snap.get("memory_mb") is not None:
            mem_samples.append(float(snap["memory_mb"]))
        time.sleep(max(0.0, interval_s))

    elapsed = time.perf_counter() - t0
    lat_sorted = sorted(latencies)
    p50 = lat_sorted[len(lat_sorted) // 2] if lat_sorted else 0.0
    p95 = lat_sorted[int(len(lat_sorted) * 0.95) - 1] if lat_sorted else 0.0
    mem_growth = None
    if len(mem_samples) >= 2:
        mem_growth = round(mem_samples[-1] - mem_samples[0], 3)

    return {
        "ok": errors == 0,
        "label": label,
        "duration_s_requested": duration_s,
        "elapsed_s": round(elapsed, 4),
        "requests": requests,
        "errors": errors,
        "latency_ms": {
            "avg": round(sum(latencies) / max(len(latencies), 1), 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "max": round(max(latencies) if latencies else 0.0, 3),
        },
        "memory_mb_growth": mem_growth,
        "staging_24h_complete": False,
        "note": "Timed local soak only. RC1 requires separate 24-hour staging soak.",
    }


def staging_24h_status() -> dict[str, Any]:
    """Explicit gate — 24h staging soak is not claimed complete by this process."""
    return {
        "phase": "phase_7_soak_24h",
        "complete": False,
        "required_hours": 24,
        "environment": "staging",
        "blocking": True,
        "message": (
            "24-hour staging soak has not been executed in this certification run. "
            "RC1 exit criteria require completed soak with memory growth, latency drift, "
            "error count, and audit completeness evidence."
        ),
    }
