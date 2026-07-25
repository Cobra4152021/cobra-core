"""
Adaptive Intelligence Router (AIR) — deterministic, policy-driven selection.

Order (fixed, not learned):
  1. Required capabilities
  2. Health
  3. Policy (live preference, exclusions, operator preference)
  4. Cost
  5. Latency
  6. Stable tiebreak (provider_id, model_id)
"""

from __future__ import annotations

import time
from typing import Any, NoReturn

from cobra_core.air.audit import AIR_AUDIT, AirAuditLog
from cobra_core.air.errors import AirRoutingError, AirRoutingFailureCode
from cobra_core.air.metrics import AIR_METRICS, AirMetrics, monotonic_ms
from cobra_core.air.policy import AirPolicyConfig, default_air_policy
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.types import (
    AirDecision,
    AirRequest,
    ModelDescriptor,
    budget_rank,
    cost_class_rank,
    health_rank,
    latency_class_rank,
)
from cobra_core.cial.health import is_routable_health


class AdaptiveRouter:
    """Select exactly one provider/model for an AirRequest (fail closed)."""

    def __init__(
        self,
        registry: DescriptorRegistry,
        *,
        policy: AirPolicyConfig | None = None,
        audit: AirAuditLog | None = None,
        metrics: AirMetrics | None = None,
    ) -> None:
        self.registry = registry
        self.policy = policy if policy is not None else default_air_policy()
        # Use `is None` — AirAuditLog/AirMetrics define __len__ and are falsy when empty.
        self.audit = audit if audit is not None else AIR_AUDIT
        self.metrics = metrics if metrics is not None else AIR_METRICS

    def route(self, request: AirRequest) -> AirDecision:
        """
        Return one routing decision or raise AirRoutingError.

        Never silently selects a model lacking required capabilities.
        """
        t0 = monotonic_ms()
        now_ms = int(time.time() * 1000)
        models = [m for m in self.registry.list_models() if m.enabled]
        if not models:
            return self._fail(
                request,
                AirRoutingFailureCode.EMPTY_REGISTRY,
                "no models registered in AIR catalog",
                now_ms,
                t0,
            )

        # 1. Required capabilities
        required = request.capabilities
        capable = [m for m in models if m.has_capabilities(required)]
        if not capable:
            return self._fail(
                request,
                AirRoutingFailureCode.NO_CAPABILITY_MATCH,
                "no provider satisfies required capabilities",
                now_ms,
                t0,
            )

        # 2. Health (exclude unavailable/disabled)
        healthy = [m for m in capable if is_routable_health(m.health)]
        if not healthy:
            return self._fail(
                request,
                AirRoutingFailureCode.NO_HEALTHY_CANDIDATE,
                "no healthy provider for required capabilities",
                now_ms,
                t0,
                health_related=True,
            )

        # 3. Policy filters
        candidates = self._apply_policy(request, healthy)
        if not candidates:
            return self._fail(
                request,
                AirRoutingFailureCode.POLICY_EXCLUDED,
                "all capability-matched providers excluded by policy",
                now_ms,
                t0,
            )

        requires_live = bool(request.metadata.get("requires_live"))
        allow_offline = bool(request.metadata.get("allow_offline_fallback", True))
        if requires_live and self.policy.prefer_live_when_required:
            live = [m for m in candidates if m.requires_live]
            if live:
                candidates = live
            elif not allow_offline:
                return self._fail(
                    request,
                    AirRoutingFailureCode.LIVE_REQUIRED_UNAVAILABLE,
                    "live provider required but unavailable",
                    now_ms,
                    t0,
                )

        chosen = self._select(request, candidates)
        reason = self._reason(request, chosen, requires_live=requires_live)
        decision = AirDecision(
            profile_id=request.profile_id,
            requested_capabilities=request.capabilities,
            provider_id=chosen.provider_id,
            model_id=chosen.model_id,
            reason=reason,
            health_state=chosen.health,
            estimated_cost_class=chosen.estimated_cost,
            latency_class=chosen.latency,
            timestamp_ms=now_ms,
            policy_id=self.policy.policy_id,
            task=request.task,
            priority=request.priority,
            budget=request.budget,
            requested_latency=request.latency,
            correlation_id=request.correlation_id or "",
        )
        elapsed = max(0, monotonic_ms() - t0)
        self.audit.record(decision)
        self.metrics.record_decision(decision, latency_ms=elapsed)
        return decision

    def _apply_policy(
        self, request: AirRequest, models: list[ModelDescriptor]
    ) -> list[ModelDescriptor]:
        out: list[ModelDescriptor] = []
        for model in models:
            if model.provider_id in self.policy.excluded_providers:
                continue
            if model.key in self.policy.excluded_models:
                continue
            out.append(model)
        return out

    def _select(self, request: AirRequest, candidates: list[ModelDescriptor]) -> ModelDescriptor:
        """
        Sort by: health → policy preference → cost vs budget → latency → tiebreak.
        """
        max_cost = budget_rank(request.budget)
        want_latency = latency_class_rank(request.latency)

        def sort_key(m: ModelDescriptor) -> tuple[Any, ...]:
            cost_r = cost_class_rank(m.estimated_cost)
            over_budget = 0 if cost_r <= max_cost else 1
            lat_r = latency_class_rank(m.latency)
            latency_penalty = 0 if lat_r <= want_latency else (lat_r - want_latency)
            pref = self.policy.provider_preference.get(m.provider_id, 100)
            return (
                health_rank(m.health) if self.policy.prefer_healthy_over_degraded else 0,
                pref,
                over_budget,
                cost_r,
                latency_penalty,
                lat_r,
                m.provider_id,
                m.model_id,
            )

        return sorted(candidates, key=sort_key)[0]

    def _reason(
        self,
        request: AirRequest,
        chosen: ModelDescriptor,
        *,
        requires_live: bool,
    ) -> str:
        parts = [
            "air_v1",
            f"caps={len(request.capabilities)}",
            f"health={chosen.health.value}",
            f"cost={chosen.estimated_cost.value}",
            f"latency={chosen.latency.value}",
            f"budget={request.budget.value}",
        ]
        if requires_live and chosen.requires_live:
            parts.append("live_preferred")
        elif requires_live and not chosen.requires_live:
            parts.append("offline_fallback")
        return "|".join(parts)

    def _fail(
        self,
        request: AirRequest,
        code: AirRoutingFailureCode,
        message: str,
        timestamp_ms: int,
        t0: int,
        *,
        health_related: bool = False,
    ) -> NoReturn:
        elapsed = max(0, monotonic_ms() - t0)
        self.audit.record_failure(
            profile_id=request.profile_id,
            capabilities=request.capabilities,
            air_code=code.value,
            message=message,
            timestamp_ms=timestamp_ms,
            task=request.task,
            correlation_id=request.correlation_id or "",
            policy_id=self.policy.policy_id,
        )
        self.metrics.record_failure(
            air_code=code.value,
            health_related=health_related,
            latency_ms=elapsed,
        )
        raise AirRoutingError(code, message)
