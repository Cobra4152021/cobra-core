"""Deterministic load-test harness — 100 / 500 / 1000 / 5000 simulated API requests."""

from __future__ import annotations

import time
from typing import Any

from cobra_core.api.router import API_GATEWAY, ApiRequest
from cobra_core.production.audit import PRODUCTION_AUDIT
from cobra_core.production.performance import PERFORMANCE


def _one_request(i: int) -> tuple[bool, float]:
    t0 = time.perf_counter()
    resp = API_GATEWAY.dispatch(
        ApiRequest(
            method="GET",
            path="/api/v1/status",
            request_id=f"load_{i}",
            authenticated=True,
            principal_id="svc_loadtest",
            organization_id="org_load",
            api_client_id="client_load",
            headers={"X-Cobra-Sdk-Version": "loadtest/1.0"},
        )
    )
    ms = (time.perf_counter() - t0) * 1000
    PERFORMANCE.sample(api_latency_ms=ms, request_latency_ms=ms)
    return resp.status == 200, ms


def run_load_test(n: int = 100) -> dict[str, Any]:
    if n not in {100, 500, 1000, 5000}:
        # Allow other sizes in tests but document standard sizes
        pass
    # Avoid rate-limit interference for harness: reset limiter
    from cobra_core.api.rate_limit import RATE_LIMITER

    RATE_LIMITER.reset_for_tests()
    RATE_LIMITER.org_limit = max(RATE_LIMITER.org_limit, n + 10)
    RATE_LIMITER.client_limit = max(RATE_LIMITER.client_limit, n + 10)

    latencies: list[float] = []
    errors = 0
    t0 = time.perf_counter()
    for i in range(n):
        ok, ms = _one_request(i)
        latencies.append(ms)
        if not ok:
            errors += 1
    elapsed = time.perf_counter() - t0
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[len(latencies_sorted) // 2] if latencies_sorted else 0.0
    p95 = latencies_sorted[int(len(latencies_sorted) * 0.95) - 1] if latencies_sorted else 0.0
    report = {
        "ok": errors == 0,
        "requests": n,
        "errors": errors,
        "elapsed_s": round(elapsed, 4),
        "latency_ms": {
            "avg": round(sum(latencies) / max(len(latencies), 1), 3),
            "p50": round(p50, 3),
            "p95": round(p95, 3),
            "max": round(max(latencies) if latencies else 0.0, 3),
        },
        "resource_consumption": PERFORMANCE.snapshot(),
    }
    PRODUCTION_AUDIT.record(
        "load_test",
        result="ok" if report["ok"] else "failed",
        requests=n,
        errors=errors,
    )
    return report


def run_standard_suite() -> dict[str, Any]:
    results = {str(n): run_load_test(n) for n in (100, 500, 1000)}
    return {
        "ok": all(r["ok"] for r in results.values()),
        "sizes": results,
    }


def run_rc1_suite() -> dict[str, Any]:
    """RC1 performance pack including 5000-request load."""
    results = {str(n): run_load_test(n) for n in (100, 500, 1000, 5000)}
    return {
        "ok": all(r["ok"] for r in results.values()),
        "sizes": results,
    }
