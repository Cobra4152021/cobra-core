"""
Authenticated AIR diagnostic HTTP handlers (staging ops).

Does not alter Protocol V1 chat/completions wire. Never returns prompts/secrets.
"""

from __future__ import annotations

from typing import Any

from cobra_core.air.audit import AIR_AUDIT
from cobra_core.air.bridge import (
    air_request_for_config,
    build_adaptive_router,
    catalog_for_config,
    safe_catalog_snapshot,
)
from cobra_core.air.capabilities import parse_air_capabilities
from cobra_core.air.errors import AirRoutingError
from cobra_core.air.metrics import AIR_METRICS
from cobra_core.air.policy import AirPolicyConfig, load_air_policy
from cobra_core.air.types import BudgetClass, LatencyClass, PriorityClass
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import _air_enabled


def handle_air_catalog(*, config: CialConfig | None = None) -> dict[str, Any]:
    cfg = config or load_cial_config()
    snap = safe_catalog_snapshot(cfg)
    snap["air_enabled"] = _air_enabled()
    return snap


def handle_air_audit(
    *,
    limit: int = 50,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    if correlation_id:
        entries = AIR_AUDIT.lookup(correlation_id)
    else:
        entries = AIR_AUDIT.recent(max(1, min(limit, 200)))
    return {"count": len(entries), "entries": entries}


def handle_air_metrics_json() -> dict[str, Any]:
    return AIR_METRICS.snapshot()


def handle_air_route(
    payload: dict[str, Any],
    *,
    config: CialConfig | None = None,
    correlation_id: str = "",
) -> tuple[int, dict[str, Any]]:
    """
    Capability-based routing decision (dry-run; no inference).

    Body example:
      {"capabilities":["text","offline"],"priority":"normal","budget":"low",
       "latency":"normal","task":"general","profile_id":"default"}
    """
    cfg = config or load_cial_config()
    if not _air_enabled():
        return 503, {
            "ok": False,
            "error": {
                "code": "air_disabled",
                "message": "AIR_ENABLED=false; legacy DeterministicRouter is active",
            },
        }

    caps_raw = payload.get("capabilities")
    if not isinstance(caps_raw, list) or not caps_raw:
        return 400, {
            "ok": False,
            "error": {"code": "bad_request", "message": "capabilities list required"},
        }
    try:
        caps = parse_air_capabilities([str(c) for c in caps_raw])
    except ValueError as exc:
        return 400, {
            "ok": False,
            "error": {"code": "unknown_capability", "message": str(exc)[:160]},
        }

    rid = (
        correlation_id
        or str(payload.get("correlation_id") or "").strip()
        or str(payload.get("request_id") or "").strip()
    )
    try:
        priority = PriorityClass(str(payload.get("priority") or "normal").lower())
        budget = BudgetClass(str(payload.get("budget") or "normal").lower())
        latency = LatencyClass(str(payload.get("latency") or "normal").lower())
    except ValueError:
        return 400, {
            "ok": False,
            "error": {"code": "bad_request", "message": "invalid priority/budget/latency"},
        }

    profile_id = str(payload.get("profile_id") or cfg.active_profile).strip().lower()
    # Temporarily view profile for metadata; request uses override caps.
    req_cfg = cfg
    if profile_id != cfg.active_profile:
        from dataclasses import replace

        req_cfg = replace(cfg, active_profile=profile_id)

    req = air_request_for_config(
        req_cfg,
        capabilities_override=caps,
        correlation_id=rid,
        priority=priority,
        budget=budget,
        latency=latency,
        task=str(payload.get("task") or "capability_request"),
    )

    policy = load_air_policy()
    excluded = payload.get("excluded_providers")
    if isinstance(excluded, list) and excluded:
        policy = AirPolicyConfig(
            policy_id=policy.policy_id,
            prefer_live_when_required=policy.prefer_live_when_required,
            prefer_healthy_over_degraded=policy.prefer_healthy_over_degraded,
            provider_preference=dict(policy.provider_preference),
            excluded_providers=frozenset(str(x).strip().lower() for x in excluded if str(x).strip())
            | set(policy.excluded_providers),
            excluded_models=policy.excluded_models,
            metadata=dict(policy.metadata),
        )

    # Optional: force requires_live for research-style checks
    if payload.get("requires_live") is True:
        meta = dict(req.metadata)
        meta["requires_live"] = True
        meta["allow_offline_fallback"] = bool(payload.get("allow_offline_fallback", False))
        from cobra_core.air.types import AirRequest

        req = AirRequest(
            task=req.task,
            capabilities=req.capabilities,
            priority=req.priority,
            budget=req.budget,
            latency=req.latency,
            profile_id=req.profile_id,
            correlation_id=req.correlation_id,
            metadata=meta,
        )

    router = build_adaptive_router(req_cfg, policy=policy, registry=catalog_for_config(cfg))
    try:
        decision = router.route(req)
    except AirRoutingError as exc:
        return 422, {
            "ok": False,
            "error": {
                "code": exc.air_code.value,
                "cial_code": exc.code.value,
                "message": exc.message,
            },
            "correlation_id": rid or None,
            "catalog_providers": [p.provider_id for p in catalog_for_config(cfg).list_providers()],
        }

    return 200, {
        "ok": True,
        "decision": {
            "policy_id": decision.policy_id,
            "profile": decision.profile_id,
            "requested_capabilities": sorted(c.value for c in decision.requested_capabilities),
            "selected_provider": decision.provider_id,
            "selected_model": decision.model_id,
            "selection_reason": decision.reason,
            "health_snapshot": decision.health_state.value,
            "estimated_cost_class": decision.estimated_cost_class.value,
            "latency_class": decision.latency_class.value,
            "routing_timestamp": decision.timestamp_ms,
            "correlation_id": decision.correlation_id or None,
        },
        "catalog_providers": [p.provider_id for p in catalog_for_config(cfg).list_providers()],
    }
