"""
Resilience Execution Layer — executes an AIR-selected route safely.

Does not replace AIR. Bounded retries, circuit breaker, constrained fallback,
budget checks before paid calls, idempotency, cooperative cancellation.
"""

from __future__ import annotations

import random
import threading
import time
from collections.abc import Callable
from typing import Any

from cobra_core.air.bridge import catalog_for_config
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.types import InferenceResult
from cobra_core.resilience.audit import RRF_AUDIT, ResilienceAuditLog
from cobra_core.resilience.backoff import compute_backoff_ms
from cobra_core.resilience.budget import GLOBAL_BUDGET, BudgetLedger, estimate_attempt_cost
from cobra_core.resilience.circuit_breaker import CircuitBreakerRegistry
from cobra_core.resilience.config import ResilienceConfig, load_resilience_config
from cobra_core.resilience.errors import FailureCategory, ResilienceError, traits_for
from cobra_core.resilience.fallback import evaluate_fallback
from cobra_core.resilience.health import HealthTracker
from cobra_core.resilience.idempotency import IDEMPOTENCY_STORE, IdempotencyStore
from cobra_core.resilience.metrics import RRF_METRICS, ResilienceMetrics
from cobra_core.resilience.policy import classify_exception
from cobra_core.resilience.retry import should_retry
from cobra_core.resilience.timeouts import Deadline
from cobra_core.resilience.types import (
    AttemptRecord,
    ExecutionStatus,
    ResilienceRequest,
    ResilienceResult,
    RouteTarget,
)

ProviderCallFn = Callable[..., InferenceResult]


class ResilienceExecutor:
    def __init__(
        self,
        *,
        cfg: ResilienceConfig | None = None,
        cial_config: CialConfig | None = None,
        provider_call: ProviderCallFn | None = None,
        catalog: DescriptorRegistry | None = None,
        audit: ResilienceAuditLog | None = None,
        metrics: ResilienceMetrics | None = None,
        budget: BudgetLedger | None = None,
        idempotency: IdempotencyStore | None = None,
        sleep_fn: Callable[[float], None] | None = None,
    ) -> None:
        self.cfg = cfg or load_resilience_config()
        self.cial_config = cial_config or load_cial_config()
        self.provider_call = provider_call
        self.catalog = catalog or catalog_for_config(self.cial_config)
        self.audit = audit if audit is not None else RRF_AUDIT
        self.metrics = metrics if metrics is not None else RRF_METRICS
        self.budget = budget if budget is not None else GLOBAL_BUDGET
        self.idempotency = idempotency if idempotency is not None else IDEMPOTENCY_STORE
        self.sleep_fn = sleep_fn or time.sleep
        self.rng = random.Random(self.cfg.jitter_seed)

        def _on_transition(key: str, old: Any, new: Any) -> None:
            self.metrics.record_circuit_transition()
            if str(new) == "open":
                self.metrics.record_circuit_open()
            self.audit.record(
                {
                    "event": "circuit_transition",
                    "circuit_key": key,
                    "circuit_state_before": str(old),
                    "circuit_state_after": str(new),
                }
            )

        self.circuits = CircuitBreakerRegistry(self.cfg, on_transition=_on_transition)
        self.health = HealthTracker(self.circuits)

    def execute(
        self,
        request: ResilienceRequest,
        *,
        messages: list[dict[str, Any]],
        max_tokens: int,
        cancel_event: threading.Event | None = None,
        parse_structured: Callable[[str], dict[str, Any]] | None = None,
        repair_messages_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    ) -> ResilienceResult:
        """
        Execute primary route with bounded retry; optional one schema repair;
        optional constrained fallback. Max provider calls enforced.
        """
        t0 = time.perf_counter()
        deadline = Deadline(self.cfg.request_deadline_ms)
        attempts: list[AttemptRecord] = []
        provider_calls = 0
        request_spent = 0.0
        total_backoff = 0
        retries = 0
        schema_repair_count = 0
        fallback_used = False
        current = request.primary

        cached = self.idempotency.get(request.execution_id)
        if cached is not None:
            self.metrics.record_execution(
                skill_id=request.skill_id,
                provider_id=str(cached.get("provider_id") or "none"),
                result="success",
                failure_category=None,
                success=True,
                idempotency_hit=True,
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return ResilienceResult(
                status=ExecutionStatus.SUCCESS,
                content=str(cached.get("content") or ""),
                provider_id=str(cached.get("provider_id") or ""),
                model_id=str(cached.get("model_id") or ""),
                prompt_tokens=int(cached.get("prompt_tokens") or 0),
                completion_tokens=int(cached.get("completion_tokens") or 0),
                attempts=[],
                execution_id=request.execution_id,
                idempotency_hit=True,
                metadata={"cached": True},
            )

        def cancelled() -> bool:
            return cancel_event is not None and cancel_event.is_set()

        def audit_attempt(**fields: Any) -> None:
            self.audit.record(
                {
                    "correlation_id": request.correlation_id or None,
                    "execution_id": request.execution_id,
                    "skill_id": request.skill_id,
                    "skill_version": request.skill_version,
                    "profile": request.profile_id,
                    **fields,
                }
            )

        # --- Phase A: primary + transport retries ---
        last_failure: ResilienceError | None = None
        content = ""
        prompt_tokens = 0
        completion_tokens = 0
        success = False

        for attempt_num in range(1, self.cfg.max_attempts + 1):
            if cancelled():
                return self._fail(
                    request,
                    attempts,
                    FailureCategory.CANCELLED,
                    t0,
                    retries=retries,
                    total_backoff=total_backoff,
                    provider_calls=provider_calls,
                    cancelled=True,
                )
            if deadline.expired():
                return self._fail(
                    request,
                    attempts,
                    FailureCategory.REQUEST_DEADLINE_EXCEEDED,
                    t0,
                    retries=retries,
                    total_backoff=total_backoff,
                    provider_calls=provider_calls,
                )
            if provider_calls >= self.cfg.max_provider_calls:
                break

            br = self.circuits.get(current.provider_id, current.model_id)
            allowed, circ_before = br.allow_request()
            if not allowed:
                last_failure = ResilienceError(FailureCategory.CIRCUIT_OPEN)
                attempts.append(
                    AttemptRecord(
                        attempt_number=attempt_num,
                        provider_id=current.provider_id,
                        model_id=current.model_id,
                        failure_category=FailureCategory.CIRCUIT_OPEN,
                        circuit_state_before=str(circ_before),
                        circuit_state_after=str(circ_before),
                        retry_decision="blocked_circuit_open",
                    )
                )
                audit_attempt(
                    provider=current.provider_id,
                    model=current.model_id,
                    attempt_number=attempt_num,
                    failure_category=FailureCategory.CIRCUIT_OPEN.value,
                    retry_decision="blocked",
                    circuit_state_before=str(circ_before),
                    circuit_state_after=str(circ_before),
                    final_execution_status=ExecutionStatus.CIRCUIT_OPEN.value,
                    deadline_remaining_ms=deadline.remaining_ms(),
                )
                break

            est = estimate_attempt_cost(
                current.provider_id,
                current.model_id,
                input_tokens=min(request.estimated_input_tokens, self.cfg.max_input_tokens),
                output_ceiling=min(max_tokens, self.cfg.max_output_tokens),
            )
            try:
                self.budget.assert_can_spend(
                    self.cfg, request_spent=request_spent, estimated_next=est
                )
            except ResilienceError as bexc:
                last_failure = bexc
                attempts.append(
                    AttemptRecord(
                        attempt_number=attempt_num,
                        provider_id=current.provider_id,
                        model_id=current.model_id,
                        failure_category=bexc.category,
                        estimated_cost_usd=est,
                        circuit_state_before=str(circ_before),
                        retry_decision="budget_block",
                    )
                )
                return self._fail(
                    request,
                    attempts,
                    bexc.category,
                    t0,
                    retries=retries,
                    total_backoff=total_backoff,
                    provider_calls=provider_calls,
                    budget_exceeded=True,
                )

            try:
                provider_calls += 1
                result = self._call(
                    current,
                    messages=messages,
                    max_tokens=max_tokens,
                    cancel_event=cancel_event,
                    timeout_ms=deadline.child_timeout_ms(self.cfg.provider_timeout_ms),
                    metadata={
                        "correlation_id": request.correlation_id,
                        "skill_id": request.skill_id,
                        "execution_id": request.execution_id,
                    },
                )
                content = result.content or ""
                prompt_tokens = result.prompt_tokens
                completion_tokens = result.completion_tokens
                request_spent += est
                self.budget.record(est)
                circ_after = br.record_success()
                self.health.record_outcome(current.provider_id, current.model_id, success=True)
                attempts.append(
                    AttemptRecord(
                        attempt_number=attempt_num,
                        provider_id=current.provider_id,
                        model_id=current.model_id,
                        success=True,
                        estimated_cost_usd=est,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        latency_ms=result.inference_ms,
                        circuit_state_before=str(circ_before),
                        circuit_state_after=str(circ_after),
                        retry_decision="success",
                    )
                )
                success = True
                last_failure = None
                break
            except Exception as exc:  # noqa: BLE001
                rerr = classify_exception(exc)
                last_failure = rerr
                circ_after = circ_before
                if traits_for(rerr.category).circuit_breaker_relevant:
                    circ_after = br.record_failure()
                    self.health.record_outcome(current.provider_id, current.model_id, success=False)
                retry_ok, retry_reason = should_retry(
                    rerr.category,
                    attempts_so_far=attempt_num,
                    cfg=self.cfg,
                    remaining_deadline_ms=deadline.remaining_ms(),
                    retry_after_ms=rerr.retry_after_ms,
                )
                backoff = 0
                if retry_ok:
                    backoff = compute_backoff_ms(
                        attempt_num - 1,
                        initial_ms=self.cfg.initial_backoff_ms,
                        max_ms=self.cfg.max_backoff_ms,
                        retry_after_ms=rerr.retry_after_ms,
                        remaining_deadline_ms=deadline.remaining_ms(),
                        rng=self.rng,
                    )
                    total_backoff += backoff
                    retries += 1
                    if backoff > 0 and not cancelled():
                        self.sleep_fn(backoff / 1000.0)
                attempts.append(
                    AttemptRecord(
                        attempt_number=attempt_num,
                        provider_id=current.provider_id,
                        model_id=current.model_id,
                        failure_category=rerr.category,
                        retry_decision=retry_reason,
                        backoff_ms=backoff,
                        circuit_state_before=str(circ_before),
                        circuit_state_after=str(circ_after),
                        estimated_cost_usd=0.0,
                    )
                )
                audit_attempt(
                    provider=current.provider_id,
                    model=current.model_id,
                    attempt_number=attempt_num,
                    failure_category=rerr.category.value,
                    retry_decision=retry_reason,
                    backoff_ms=backoff,
                    circuit_state_before=str(circ_before),
                    circuit_state_after=str(circ_after),
                    budget_remaining=self.budget.remaining(
                        self.cfg, request_spent=request_spent
                    ).get("request"),
                    deadline_remaining_ms=deadline.remaining_ms(),
                    schema_repair_attempt=False,
                )
                if not retry_ok:
                    break

        # --- Phase B: one schema repair (counts toward provider call ceiling) ---
        if (
            success
            and parse_structured is not None
            and repair_messages_fn is not None
            and provider_calls < self.cfg.max_provider_calls
            and schema_repair_count < self.cfg.max_repair_attempts
        ):
            try:
                parse_structured(content)
            except Exception:  # noqa: BLE001 — structured invalid → one repair
                if cancelled() or deadline.expired():
                    return self._fail(
                        request,
                        attempts,
                        FailureCategory.CANCELLED
                        if cancelled()
                        else FailureCategory.REQUEST_DEADLINE_EXCEEDED,
                        t0,
                        retries=retries,
                        total_backoff=total_backoff,
                        provider_calls=provider_calls,
                        cancelled=cancelled(),
                    )
                schema_repair_count = 1
                try:
                    est = estimate_attempt_cost(
                        current.provider_id,
                        current.model_id,
                        input_tokens=request.estimated_input_tokens,
                        output_ceiling=max_tokens,
                    )
                    self.budget.assert_can_spend(
                        self.cfg, request_spent=request_spent, estimated_next=est
                    )
                    provider_calls += 1
                    repair_msgs = repair_messages_fn(content)
                    result = self._call(
                        current,
                        messages=repair_msgs,
                        max_tokens=max_tokens,
                        cancel_event=cancel_event,
                        timeout_ms=deadline.child_timeout_ms(self.cfg.provider_timeout_ms),
                        metadata={
                            "correlation_id": request.correlation_id,
                            "skill_id": request.skill_id,
                            "schema_repair": True,
                        },
                    )
                    content = result.content or ""
                    prompt_tokens += result.prompt_tokens
                    completion_tokens += result.completion_tokens
                    request_spent += est
                    self.budget.record(est)
                    parse_structured(content)  # must validate
                    attempts.append(
                        AttemptRecord(
                            attempt_number=len(attempts) + 1,
                            provider_id=current.provider_id,
                            model_id=current.model_id,
                            success=True,
                            schema_repair_attempt=True,
                            estimated_cost_usd=est,
                        )
                    )
                    audit_attempt(
                        provider=current.provider_id,
                        model=current.model_id,
                        attempt_number=len(attempts),
                        schema_repair_attempt=True,
                        retry_decision="schema_repair_success",
                        failure_category=None,
                        deadline_remaining_ms=deadline.remaining_ms(),
                    )
                except Exception:  # noqa: BLE001
                    success = False
                    last_failure = ResilienceError(FailureCategory.SCHEMA_REPAIR_FAILED)
                    attempts.append(
                        AttemptRecord(
                            attempt_number=len(attempts) + 1,
                            provider_id=current.provider_id,
                            model_id=current.model_id,
                            success=False,
                            schema_repair_attempt=True,
                            failure_category=FailureCategory.SCHEMA_REPAIR_FAILED,
                        )
                    )

        # --- Phase C: constrained fallback (one alternative; reevaluate live gate) ---
        if not success and last_failure is not None and not cancelled():
            live_open = bool(self.cial_config.can_use_live_provider)
            fb = evaluate_fallback(
                cfg=self.cfg,
                failure=last_failure.category,
                required=request.required_capabilities,
                primary=request.primary,
                catalog=self.catalog,
                allow_offline_fallback=request.allow_offline_fallback,
                live_gate_open=live_open,
                circuit_allows=lambda p, m: str(self.circuits.get(p, m).current_state()) != "open",
            )
            audit_attempt(
                provider=request.primary.provider_id,
                model=request.primary.model_id,
                attempt_number=len(attempts) + 1,
                failure_category=last_failure.category.value,
                fallback_decision=fb.reason,
                fallback_provider=(fb.target.provider_id if fb.target else None),
                fallback_model=(fb.target.model_id if fb.target else None),
                deadline_remaining_ms=deadline.remaining_ms(),
            )
            if (
                fb.allowed
                and fb.target is not None
                and provider_calls < self.cfg.max_provider_calls
            ):
                # Reevaluate live gate before calling
                if fb.target.provider_id == "openai" and not self.cial_config.can_use_live_provider:
                    last_failure = ResilienceError(FailureCategory.OPERATOR_DISABLED)
                else:
                    current = fb.target
                    fallback_used = True
                    try:
                        est = estimate_attempt_cost(
                            current.provider_id,
                            current.model_id,
                            input_tokens=request.estimated_input_tokens,
                            output_ceiling=max_tokens,
                        )
                        self.budget.assert_can_spend(
                            self.cfg, request_spent=request_spent, estimated_next=est
                        )
                        br = self.circuits.get(current.provider_id, current.model_id)
                        allowed, circ_before = br.allow_request()
                        if not allowed:
                            last_failure = ResilienceError(FailureCategory.CIRCUIT_OPEN)
                        else:
                            provider_calls += 1
                            result = self._call(
                                current,
                                messages=messages,
                                max_tokens=max_tokens,
                                cancel_event=cancel_event,
                                timeout_ms=deadline.child_timeout_ms(self.cfg.provider_timeout_ms),
                                metadata={
                                    "correlation_id": request.correlation_id,
                                    "fallback": True,
                                },
                            )
                            content = result.content or ""
                            if parse_structured is not None:
                                parse_structured(content)
                            prompt_tokens = result.prompt_tokens
                            completion_tokens = result.completion_tokens
                            request_spent += est
                            self.budget.record(est)
                            br.record_success()
                            success = True
                            last_failure = None
                            attempts.append(
                                AttemptRecord(
                                    attempt_number=len(attempts) + 1,
                                    provider_id=current.provider_id,
                                    model_id=current.model_id,
                                    success=True,
                                    estimated_cost_usd=est,
                                    retry_decision="fallback_success",
                                    circuit_state_before=str(circ_before),
                                )
                            )
                    except Exception as exc:  # noqa: BLE001
                        last_failure = classify_exception(exc)
                        attempts.append(
                            AttemptRecord(
                                attempt_number=len(attempts) + 1,
                                provider_id=current.provider_id,
                                model_id=current.model_id,
                                failure_category=last_failure.category,
                                retry_decision="fallback_failure",
                            )
                        )

        if success:
            self.idempotency.put(
                request.execution_id,
                {
                    "content": content,
                    "provider_id": current.provider_id,
                    "model_id": current.model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                },
            )
            latency = int((time.perf_counter() - t0) * 1000)
            self.metrics.record_execution(
                skill_id=request.skill_id,
                provider_id=current.provider_id,
                result="success",
                failure_category=None,
                success=True,
                retries=retries,
                backoff_ms=total_backoff,
                fallback_attempted=fallback_used,
                fallback_success=fallback_used,
                latency_ms=latency,
                provider_attempts=provider_calls,
                provider_latency_ms=sum(a.latency_ms for a in attempts),
            )
            audit_attempt(
                provider=current.provider_id,
                model=current.model_id,
                attempt_number=len(attempts),
                final_execution_status=ExecutionStatus.SUCCESS.value,
                fallback_decision="used" if fallback_used else "none",
                schema_repair_attempt=schema_repair_count > 0,
                deadline_remaining_ms=deadline.remaining_ms(),
            )
            return ResilienceResult(
                status=ExecutionStatus.SUCCESS,
                content=content,
                provider_id=current.provider_id,
                model_id=current.model_id,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                attempts=attempts,
                schema_repair_count=schema_repair_count,
                fallback_used=fallback_used,
                total_estimated_cost_usd=request_spent,
                execution_id=request.execution_id,
            )

        cat = last_failure.category if last_failure else FailureCategory.INTERNAL_EXECUTION_ERROR
        return self._fail(
            request,
            attempts,
            cat,
            t0,
            retries=retries,
            total_backoff=total_backoff,
            provider_calls=provider_calls,
            fallback_attempted=fallback_used,
            retry_exhausted=retries > 0 and cat != FailureCategory.CANCELLED,
        )

    def _call(
        self,
        target: RouteTarget,
        *,
        messages: list[dict[str, Any]],
        max_tokens: int,
        cancel_event: threading.Event | None,
        timeout_ms: int,
        metadata: dict[str, Any],
    ) -> InferenceResult:
        if self.provider_call is None:
            raise ResilienceError(
                FailureCategory.INTERNAL_EXECUTION_ERROR,
                "no provider_call configured",
            )
        if cancel_event is not None and cancel_event.is_set():
            raise ResilienceError(FailureCategory.CANCELLED)
        return self.provider_call(
            provider_id=target.provider_id,
            model_id=target.model_id,
            messages=messages,
            max_tokens=max_tokens,
            cancel_event=cancel_event,
            timeout_ms=timeout_ms,
            metadata=metadata,
        )

    def _fail(
        self,
        request: ResilienceRequest,
        attempts: list[AttemptRecord],
        category: FailureCategory,
        t0: float,
        *,
        retries: int,
        total_backoff: int,
        provider_calls: int,
        cancelled: bool = False,
        budget_exceeded: bool = False,
        fallback_attempted: bool = False,
        retry_exhausted: bool = False,
    ) -> ResilienceResult:
        status = ExecutionStatus.FAILED
        if cancelled or category == FailureCategory.CANCELLED:
            status = ExecutionStatus.CANCELLED
        elif category == FailureCategory.BUDGET_EXCEEDED:
            status = ExecutionStatus.BUDGET_EXCEEDED
        elif category == FailureCategory.CIRCUIT_OPEN:
            status = ExecutionStatus.CIRCUIT_OPEN
        elif category == FailureCategory.REQUEST_DEADLINE_EXCEEDED:
            status = ExecutionStatus.DEADLINE_EXCEEDED
        latency = int((time.perf_counter() - t0) * 1000)
        provider = attempts[-1].provider_id if attempts else request.primary.provider_id
        self.metrics.record_execution(
            skill_id=request.skill_id,
            provider_id=provider,
            result=status.value,
            failure_category=category.value,
            success=False,
            retries=retries,
            retry_exhausted=retry_exhausted,
            backoff_ms=total_backoff,
            fallback_attempted=fallback_attempted,
            timeout=category == FailureCategory.PROVIDER_TIMEOUT,
            budget_exceeded=budget_exceeded or category == FailureCategory.BUDGET_EXCEEDED,
            cancelled=status == ExecutionStatus.CANCELLED,
            latency_ms=latency,
            provider_attempts=provider_calls,
        )
        self.audit.record(
            {
                "correlation_id": request.correlation_id or None,
                "execution_id": request.execution_id,
                "skill_id": request.skill_id,
                "skill_version": request.skill_version,
                "profile": request.profile_id,
                "provider": provider,
                "model": attempts[-1].model_id if attempts else request.primary.model_id,
                "attempt_number": len(attempts),
                "failure_category": category.value,
                "final_execution_status": status.value,
            }
        )
        return ResilienceResult(
            status=status,
            attempts=attempts,
            failure_category=category,
            execution_id=request.execution_id,
            provider_id=provider,
            model_id=attempts[-1].model_id if attempts else request.primary.model_id,
            fallback_used=fallback_attempted,
        )
