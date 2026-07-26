"""Bridge ISF provider invocation through the Resilience Execution Layer."""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any

from cobra_core.air.bridge import catalog_for_config
from cobra_core.cial.engine import CialEngine
from cobra_core.cial.types import InferenceResult
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.schemas import empty_skill_output
from cobra_core.isf.structured_json import (
    build_repair_prompt,
    parse_provider_json,
    schema_json_prompt,
    validate_or_raise,
)
from cobra_core.isf.types import SkillRequest
from cobra_core.resilience.config import load_resilience_config, rrf_enabled
from cobra_core.resilience.errors import FailureCategory, ResilienceError
from cobra_core.resilience.executor import ResilienceExecutor
from cobra_core.resilience.idempotency import make_execution_id
from cobra_core.resilience.types import (
    ExecutionStatus,
    ResilienceRequest,
    ResilienceResult,
    RouteTarget,
)


def _mock_structured_content(manifest: SkillManifest, request: SkillRequest) -> str:
    """Schema-shaped offline fill — never free-form success for structured skills."""
    evidence_types = sorted({e.evidence_type.value for e in request.evidence})
    base = empty_skill_output(
        manifest.schema_key,
        summary=(
            f"{manifest.title}: structured assessment draft "
            f"(provider=mock; evidence_types={','.join(evidence_types) or 'none'})"
        ),
        confidence=0.45,
        missing_information=[],
        recommended_next_steps=["Validate findings against source evidence"],
        needs_human_review=True,
    )
    if manifest.id == "evidence_summary":
        base["evidence_count"] = len(request.evidence)
    if manifest.id == "document_comparison":
        base["documents"] = [e.ref_id for e in request.evidence[:2]]
    return json.dumps(base)


def build_provider_call(
    cial: CialEngine | None,
    *,
    manifest: SkillManifest,
    request: SkillRequest,
) -> Callable[..., InferenceResult]:
    def provider_call(
        *,
        provider_id: str,
        model_id: str,
        messages: list[dict[str, Any]],
        max_tokens: int,
        cancel_event: threading.Event | None = None,
        timeout_ms: int = 15_000,
        metadata: dict[str, Any] | None = None,
    ) -> InferenceResult:
        if provider_id == "mock":
            # Offline-compatible structured fill (RRF still meters the attempt).
            return InferenceResult(
                content=_mock_structured_content(manifest, request),
                prompt_tokens=8,
                completion_tokens=32,
                inference_ms=1,
                cial_provider_id="mock",
                cial_model_id=model_id,
            )
        if cial is None:
            raise ResilienceError(
                FailureCategory.PROVIDER_UNAVAILABLE,
                "live provider call requested without CIAL engine",
            )
        return cial.complete_on_route(
            messages,
            max_tokens,
            provider_id=provider_id,
            model_id=model_id,
            cancel_event=cancel_event,
            metadata=metadata,
            route_reason="rrf_preselected",
        )

    return provider_call


_SHARED_EXECUTOR: ResilienceExecutor | None = None


def shared_executor(
    *,
    cial_engine: CialEngine | None,
    manifest: SkillManifest,
    request: SkillRequest,
) -> ResilienceExecutor:
    """Process-scoped executor so circuit breakers persist across requests."""
    global _SHARED_EXECUTOR
    if _SHARED_EXECUTOR is None:
        _SHARED_EXECUTOR = ResilienceExecutor(
            cfg=load_resilience_config(),
            cial_config=cial_engine.config if cial_engine else None,
        )
    _SHARED_EXECUTOR.provider_call = build_provider_call(
        cial_engine, manifest=manifest, request=request
    )
    if cial_engine is not None:
        _SHARED_EXECUTOR.cial_config = cial_engine.config
        _SHARED_EXECUTOR.catalog = catalog_for_config(cial_engine.config)
    return _SHARED_EXECUTOR


def reset_shared_executor() -> None:
    global _SHARED_EXECUTOR
    _SHARED_EXECUTOR = None


def invoke_with_rrf(
    *,
    manifest: SkillManifest,
    request: SkillRequest,
    provider_id: str,
    model_id: str,
    route_reason: str,
    cial_engine: CialEngine | None,
    executor: ResilienceExecutor | None = None,
    cancel_event: threading.Event | None = None,
) -> tuple[dict[str, Any], int, str, ResilienceResult]:
    """
    Returns (output_dict, repair_count, schema_result, rrf_result).

    Raises ResilienceError on hard transport/budget/circuit failures after policy.
    """
    if not rrf_enabled() and executor is None:
        raise RuntimeError("invoke_with_rrf called while RRF disabled")

    if executor is not None:
        execu = executor
        if execu.provider_call is None:
            execu.provider_call = build_provider_call(
                cial_engine, manifest=manifest, request=request
            )
    else:
        execu = shared_executor(cial_engine=cial_engine, manifest=manifest, request=request)

    schema_prompt = schema_json_prompt(manifest.schema_key)
    evidence_refs = [{"type": e.evidence_type.value, "ref_id": e.ref_id} for e in request.evidence]
    user_content = (
        f"Skill={manifest.id} version={manifest.version}. "
        f"Task={request.task}. Evidence refs={evidence_refs}. "
        f"{schema_prompt}"
    )
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]

    def parse_structured(raw: str) -> dict[str, Any]:
        return validate_or_raise(manifest.schema_key, parse_provider_json(raw))

    def repair_messages_fn(_prior: str) -> list[dict[str, Any]]:
        return [
            {"role": "user", "content": user_content},
            {
                "role": "user",
                "content": build_repair_prompt(
                    manifest.schema_key, prior_error="schema validation failed"
                ),
            },
        ]

    allow_offline = "offline" in manifest.supported_profiles and (
        # Never claim offline for vision-required skills.
        not any(c.value == "vision" for c in manifest.required_capabilities)
    )
    exec_id = make_execution_id(
        skill_id=manifest.id,
        skill_version=manifest.version,
        correlation_id=request.correlation_id,
        revision=str(request.metadata.get("revision") or "1"),
        profile_id=request.profile_id,
    )
    rreq = ResilienceRequest(
        execution_id=exec_id,
        correlation_id=request.correlation_id,
        skill_id=manifest.id,
        skill_version=manifest.version,
        profile_id=request.profile_id,
        required_capabilities=frozenset(manifest.required_capabilities),
        primary=RouteTarget(
            provider_id=provider_id,
            model_id=model_id,
            route_reason=route_reason,
            capabilities=frozenset(manifest.required_capabilities),
        ),
        allow_offline_fallback=allow_offline,
        allow_live_fallback=False,
        revision=str(request.metadata.get("revision") or "1"),
        estimated_input_tokens=max(64, len(user_content) // 4),
        max_output_tokens=1024,
    )
    rres = execu.execute(
        rreq,
        messages=messages,
        max_tokens=1024,
        cancel_event=cancel_event,
        parse_structured=parse_structured,
        repair_messages_fn=repair_messages_fn,
    )
    if rres.status != ExecutionStatus.SUCCESS:
        raise ResilienceError(rres.failure_category or FailureCategory.INTERNAL_EXECUTION_ERROR)
    output = parse_structured(rres.content)
    schema_result = "repaired" if rres.schema_repair_count else "valid"
    return output, rres.schema_repair_count, schema_result, rres
