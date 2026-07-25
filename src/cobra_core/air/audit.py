"""AIR decision audit trail (never records prompts or secrets)."""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import asdict
from typing import Any

from cobra_core.air.types import AirDecision


class AirAuditLog:
    """Bounded in-memory audit of routing decisions (safe fields only)."""

    def __init__(self, *, maxlen: int = 1000) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def record(self, decision: AirDecision) -> dict[str, Any]:
        entry = {
            "profile": decision.profile_id,
            "task": decision.task,
            "requested_capabilities": sorted(c.value for c in decision.requested_capabilities),
            "selected_provider": decision.provider_id,
            "selected_model": decision.model_id,
            "reason": decision.reason,
            "health_snapshot": decision.health_state.value,
            "estimated_cost_class": decision.estimated_cost_class.value,
            "latency_class": decision.latency_class.value,
            "routing_timestamp_ms": decision.timestamp_ms,
            "policy_id": decision.policy_id,
            "priority": decision.priority.value,
            "budget": decision.budget.value,
            "requested_latency": decision.requested_latency.value,
        }
        with self._lock:
            self._entries.append(entry)
        return entry

    def record_failure(
        self,
        *,
        profile_id: str,
        capabilities: frozenset[Any],
        air_code: str,
        message: str,
        timestamp_ms: int,
        task: str = "general",
    ) -> dict[str, Any]:
        entry = {
            "profile": profile_id,
            "task": task,
            "requested_capabilities": sorted(
                c.value if hasattr(c, "value") else str(c) for c in capabilities
            ),
            "selected_provider": None,
            "selected_model": None,
            "reason": f"failure:{air_code}",
            "health_snapshot": None,
            "estimated_cost_class": None,
            "latency_class": None,
            "routing_timestamp_ms": timestamp_ms,
            "failure_code": air_code,
            "failure_message": message,
        }
        with self._lock:
            self._entries.append(entry)
        return entry

    def recent(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            items = list(self._entries)
        return items[-limit:]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._entries)


def decision_to_audit_dict(decision: AirDecision) -> dict[str, Any]:
    """Serialize an AirDecision for external audit sinks (no prompts)."""
    data = asdict(decision)
    data["requested_capabilities"] = sorted(c.value for c in decision.requested_capabilities)
    data["health_state"] = decision.health_state.value
    data["estimated_cost_class"] = decision.estimated_cost_class.value
    data["latency_class"] = decision.latency_class.value
    data["priority"] = decision.priority.value
    data["budget"] = decision.budget.value
    data["requested_latency"] = decision.requested_latency.value
    return data
