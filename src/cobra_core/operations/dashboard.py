"""Admin-facing aggregation helpers (no web UI)."""

from __future__ import annotations

from typing import Any

from cobra_core.operations.alerts import alerts_public_dict
from cobra_core.operations.feature_flags import FEATURE_FLAGS
from cobra_core.operations.health import health_public_dict
from cobra_core.operations.status import status_public_dict
from cobra_core.operations.usage import USAGE


def dashboard_snapshot() -> dict[str, Any]:
    """Single composition of OCP surfaces for operators / tooling."""
    return {
        "ok": True,
        "status": status_public_dict(),
        "health": health_public_dict(),
        "usage": USAGE.to_public_dict(),
        "alerts": alerts_public_dict(),
        "feature_flags": FEATURE_FLAGS.snapshot(),
    }
