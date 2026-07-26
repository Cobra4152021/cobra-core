"""Authenticated RRF diagnostic HTTP handlers."""

from __future__ import annotations

from typing import Any

from cobra_core.resilience.audit import RRF_AUDIT
from cobra_core.resilience.config import rrf_enabled
from cobra_core.resilience.metrics import RRF_METRICS


def handle_rrf_metrics_json() -> dict[str, Any]:
    snap = RRF_METRICS.snapshot()
    snap["rrf_enabled"] = rrf_enabled()
    return snap


def handle_rrf_audit(*, limit: int = 50) -> dict[str, Any]:
    entries = RRF_AUDIT.recent(max(1, min(limit, 200)))
    return {"count": len(entries), "entries": entries, "rrf_enabled": rrf_enabled()}
