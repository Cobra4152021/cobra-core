"""
Investigation Skill Engine — expand skill → AIR → CIAL → structured result.

Computer requests a skill id. ISF expands capabilities; AIR selects provider.
Provider JSON is parsed into the skill schema (one repair attempt max).
"""

from __future__ import annotations

import time
from typing import Any

from cobra_core.air.bridge import air_request_for_config, build_adaptive_router
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.errors import AirRoutingError
from cobra_core.air.types import AirRequest, BudgetClass, LatencyClass, PriorityClass
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.isf.audit import ISF_AUDIT, IsfAuditLog
from cobra_core.isf.confidence import ConfidenceDisposition
from cobra_core.isf.enabled import isf_enabled
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import skill_evidence_gaps
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.metrics import ISF_METRICS, IsfMetrics
from cobra_core.isf.registry import SKILL_REGISTRY, SkillRegistry
from cobra_core.isf.schemas import empty_skill_output, validate_skill_output
from cobra_core.isf.structured_json import (
    build_repair_prompt,
    parse_provider_json,
    schema_json_prompt,
    validate_or_raise,
)
from cobra_core.isf.types import (
    CapabilityExpansion,
    SkillExecutionStatus,
    SkillRequest,
    SkillResult,
)
from cobra_core.isf.versioning import assert_version_compatible
from cobra_core.resilience.config import rrf_enabled
from cobra_core.resilience.errors import FailureCategory, ResilienceError
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cobra_core.resilience.executor import ResilienceExecutor


class SkillEngine:
    """Resolve skill manifests, expand capabilities, route via AIR, return typed results."""

    def __init__(
        self,
        *,
        registry: SkillRegistry | None = None,
        config: CialConfig | None = None,
        cial_engine: CialEngine | None = None,
        audit: IsfAuditLog | None = None,
        metrics: IsfMetrics | None = None,
        resilience_executor: ResilienceExecutor | None = None,
    ) -> None:
        self.registry = registry if registry is not None else SKILL_REGISTRY
        self.config = config or load_cial_config()
        self.cial_engine = cial_engine
        self.audit = audit if audit is not None else ISF_AUDIT
        self.metrics = metrics if metrics is not None else ISF_METRICS
        self.resilience_executor = resilience_executor

    def expand(self, request: SkillRequest) -> CapabilityExpansion:
        manifest = self.registry.get(request.skill_id)
        self._assert_profile(manifest, request.profile_id)
        caps = manifest.effective_capabilities()
        return CapabilityExpansion(
            skill_id=manifest.id,
            skill_version=manifest.version,
            required_capabilities=frozenset(manifest.required_capabilities),
            optional_capabilities=frozenset(manifest.optional_capabilities),
            effective_capabilities=caps,
        )

    def execute(self, request: SkillRequest) -> SkillResult:
        """
        Full skill execution path (fail closed on missing evidence / routing / bad JSON).

        Evidence is validated before any paid live call.
        """
        t0 = time.perf_counter()
        if not isf_enabled():
            raise IsfError(
                IsfErrorCode.ISF_DISABLED,
                "ISF_ENABLED=false; Investigation Skills Framework is unavailable",
            )

        try:
            manifest = self.registry.get(request.skill_id)
        except IsfError as exc:
            self._metric_fail(
                skill_id=request.skill_id or "unknown",
                status=exc.code.value,
                schema_result="skipped",
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            raise

        try:
            assert_version_compatible(request.skill_version, manifest.version)
        except IsfError as exc:
            self._metric_fail(
                skill_id=manifest.id,
                status=exc.code.value,
                schema_result="skipped",
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            raise

        self._assert_profile(manifest, request.profile_id)

        missing = skill_evidence_gaps(
            manifest.id, manifest.required_evidence_types, request.evidence
        )
        audit_base = self._audit_base_meta(manifest, request, evidence_ok=not missing)

        if missing:
            result = SkillResult(
                skill_id=manifest.id,
                skill_version=manifest.version,
                status=SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE,
                output={
                    "error": {
                        "code": IsfErrorCode.MISSING_REQUIRED_EVIDENCE.value,
                        "missing_required_evidence": [m.value for m in missing],
                    }
                },
                confidence=0.0,
                confidence_disposition=ConfidenceDisposition.NEEDS_HUMAN_REVIEW,
                expanded_capabilities=manifest.effective_capabilities(),
                missing_evidence=tuple(missing),
                correlation_id=request.correlation_id,
                needs_human_review=True,
                metadata={
                    **audit_base,
                    "evidence_validation_result": "fail",
                    "schema_validation_result": "skipped",
                    "repair_attempt_count": 0,
                },
            )
            self.audit.record(result)
            self.metrics.record(
                skill_id=manifest.id,
                status=result.status.value,
                provider_id=None,
                schema_result="skipped",
                success=False,
                missing_evidence=True,
                human_review=True,
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            return result

        expansion = self.expand(request)
        air_req = self._to_air_request(request, expansion)
        router = build_adaptive_router(self.config)
        try:
            decision = router.route(air_req)
        except AirRoutingError as exc:
            self._metric_fail(
                skill_id=manifest.id,
                status="routing_failed",
                schema_result="skipped",
                latency_ms=int((time.perf_counter() - t0) * 1000),
            )
            raise IsfError(
                IsfErrorCode.ROUTING_FAILED,
                f"AIR routing failed: {exc.air_code.value}",
            ) from exc

        mock_path = decision.provider_id == "mock"
        repair_count = 0
        schema_result = "valid"
        draft: dict[str, Any]
        selected_provider = decision.provider_id
        selected_model = decision.model_id
        route_reason = decision.reason
        rrf_meta: dict[str, Any] = {}

        use_rrf = rrf_enabled() or self.resilience_executor is not None
        if use_rrf and (self.cial_engine is not None or self.resilience_executor is not None):
            from cobra_core.isf.rrf_bridge import invoke_with_rrf

            try:
                draft, repair_count, schema_result, rres = invoke_with_rrf(
                    manifest=manifest,
                    request=request,
                    provider_id=decision.provider_id,
                    model_id=decision.model_id,
                    route_reason=decision.reason,
                    cial_engine=self.cial_engine,
                    executor=self.resilience_executor,
                )
                selected_provider = rres.provider_id or selected_provider
                selected_model = rres.model_id or selected_model
                if rres.fallback_used:
                    route_reason = f"rrf_fallback:{route_reason}"
                rrf_meta = {
                    "rrf_execution_id": rres.execution_id,
                    "rrf_attempts": len(rres.attempts),
                    "rrf_fallback_used": rres.fallback_used,
                    "rrf_schema_repair_count": rres.schema_repair_count,
                    "rrf_estimated_cost_usd": rres.total_estimated_cost_usd,
                }
            except ResilienceError as rerr:
                if rerr.category in {
                    FailureCategory.STRUCTURED_OUTPUT_INVALID,
                    FailureCategory.SCHEMA_REPAIR_FAILED,
                }:
                    schema_result = "invalid"
                    draft = {}
                    repair_count = 1
                else:
                    self._metric_fail(
                        skill_id=manifest.id,
                        status=rerr.category.value,
                        schema_result="skipped",
                        latency_ms=int((time.perf_counter() - t0) * 1000),
                    )
                    raise IsfError(
                        IsfErrorCode.EXECUTION_FAILED,
                        rerr.traits.safe_public_message,
                    ) from rerr
            if schema_result == "invalid":
                result = SkillResult(
                    skill_id=manifest.id,
                    skill_version=manifest.version,
                    status=SkillExecutionStatus.STRUCTURED_OUTPUT_INVALID,
                    output={
                        "error": {
                            "code": IsfErrorCode.STRUCTURED_OUTPUT_INVALID.value,
                            "message": "provider structured output invalid after repair",
                        }
                    },
                    confidence=0.0,
                    confidence_disposition=ConfidenceDisposition.NEEDS_HUMAN_REVIEW,
                    expanded_capabilities=expansion.effective_capabilities,
                    selected_provider=selected_provider,
                    selected_model=selected_model,
                    route_reason=route_reason,
                    correlation_id=request.correlation_id,
                    needs_human_review=True,
                    metadata={
                        **audit_base,
                        "evidence_validation_result": "pass",
                        "schema_validation_result": "invalid",
                        "repair_attempt_count": repair_count,
                        "routing_reason": route_reason,
                        "confidence_threshold": manifest.confidence_policy.minimum_confidence,
                        **rrf_meta,
                    },
                )
                self.audit.record(result)
                self.metrics.record(
                    skill_id=manifest.id,
                    status=result.status.value,
                    provider_id=selected_provider,
                    schema_result="invalid",
                    success=False,
                    schema_failure=True,
                    repair_attempted=repair_count > 0,
                    repair_failed=True,
                    human_review=True,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                )
                return result
        elif mock_path or self.cial_engine is None:
            # KC-025 offline / unit path when RRF disabled.
            draft = self._build_structured_draft(
                manifest,
                request,
                mock_path=mock_path,
                provider_id=decision.provider_id,
            )
            schema_result = "valid"
        else:
            draft, repair_count, schema_result = self._invoke_provider_structured(
                manifest,
                request,
                provider_id=decision.provider_id,
            )
            if schema_result == "invalid":
                result = SkillResult(
                    skill_id=manifest.id,
                    skill_version=manifest.version,
                    status=SkillExecutionStatus.STRUCTURED_OUTPUT_INVALID,
                    output={
                        "error": {
                            "code": IsfErrorCode.STRUCTURED_OUTPUT_INVALID.value,
                            "message": "provider structured output invalid after repair",
                        }
                    },
                    confidence=0.0,
                    confidence_disposition=ConfidenceDisposition.NEEDS_HUMAN_REVIEW,
                    expanded_capabilities=expansion.effective_capabilities,
                    selected_provider=decision.provider_id,
                    selected_model=decision.model_id,
                    route_reason=decision.reason,
                    correlation_id=request.correlation_id,
                    needs_human_review=True,
                    metadata={
                        **audit_base,
                        "evidence_validation_result": "pass",
                        "schema_validation_result": "invalid",
                        "repair_attempt_count": repair_count,
                        "routing_reason": decision.reason,
                        "confidence_threshold": manifest.confidence_policy.minimum_confidence,
                    },
                )
                self.audit.record(result)
                self.metrics.record(
                    skill_id=manifest.id,
                    status=result.status.value,
                    provider_id=decision.provider_id,
                    schema_result="invalid",
                    success=False,
                    schema_failure=True,
                    repair_attempted=repair_count > 0,
                    repair_failed=True,
                    human_review=True,
                    latency_ms=int((time.perf_counter() - t0) * 1000),
                )
                return result

        incomplete = bool(draft.get("missing_information"))
        raw_conf = float(draft.get("confidence") or 0.0)
        # Model cannot override manifest threshold — clamp then disposition from policy.
        conf = manifest.confidence_policy.clamp(
            raw_conf,
            incomplete_evidence=incomplete,
            mock_path=(selected_provider == "mock"),
        )
        disposition = manifest.confidence_policy.disposition(conf)
        needs_review = True  # human approval always required
        policy_review = disposition == ConfidenceDisposition.NEEDS_HUMAN_REVIEW
        draft["confidence"] = conf
        draft["needs_human_review"] = True
        if (
            policy_review
            and "human review required"
            not in " ".join(draft.get("recommended_next_steps") or []).lower()
        ):
            draft.setdefault("recommended_next_steps", []).append(
                "Route to human review (confidence below skill threshold)"
            )

        try:
            output = validate_skill_output(manifest.schema_key, draft)
        except Exception as exc:  # pydantic ValidationError
            raise IsfError(
                IsfErrorCode.STRUCTURED_OUTPUT_INVALID,
                "structured skill output failed schema validation",
            ) from exc

        status = (
            SkillExecutionStatus.NEEDS_HUMAN_REVIEW
            if policy_review
            else SkillExecutionStatus.COMPLETED
        )
        # Always surface needs_human_review for the approval gate.
        result = SkillResult(
            skill_id=manifest.id,
            skill_version=manifest.version,
            status=status,
            output=output,
            confidence=conf,
            confidence_disposition=disposition,
            expanded_capabilities=expansion.effective_capabilities,
            missing_evidence=(),
            selected_provider=selected_provider,
            selected_model=selected_model,
            route_reason=route_reason,
            correlation_id=request.correlation_id,
            needs_human_review=needs_review,
            metadata={
                **audit_base,
                "evidence_validation_result": "pass",
                "schema_validation_result": schema_result,
                "repair_attempt_count": repair_count,
                "routing_reason": route_reason,
                "confidence_threshold": manifest.confidence_policy.minimum_confidence,
                "policy_id": decision.policy_id,
                **rrf_meta,
            },
        )
        self.audit.record(result)
        latency_ms = int((time.perf_counter() - t0) * 1000)
        self.metrics.record(
            skill_id=manifest.id,
            status=result.status.value,
            provider_id=selected_provider,
            schema_result=schema_result,
            success=True,
            repair_attempted=repair_count > 0,
            low_confidence=policy_review,
            human_review=True,
            latency_ms=latency_ms,
        )
        return result

    def _invoke_provider_structured(
        self,
        manifest: SkillManifest,
        request: SkillRequest,
        *,
        provider_id: str,
    ) -> tuple[dict[str, Any], int, str]:
        """
        Call CIAL with schema JSON instruction; parse/validate; at most one repair.

        Returns (draft, repair_count, schema_result) where schema_result is
        valid | repaired | invalid.
        """
        assert self.cial_engine is not None
        schema_prompt = schema_json_prompt(manifest.schema_key)
        evidence_refs = [
            {"type": e.evidence_type.value, "ref_id": e.ref_id} for e in request.evidence
        ]
        user_content = (
            f"Skill={manifest.id} version={manifest.version}. "
            f"Task={request.task}. Evidence refs={evidence_refs}. "
            f"{schema_prompt}"
        )
        messages: list[dict[str, Any]] = [{"role": "user", "content": user_content}]
        meta = {
            "correlation_id": request.correlation_id,
            "skill_id": manifest.id,
            "skill_version": manifest.version,
        }
        repair_count = 0
        try:
            inf = self.cial_engine.complete(
                messages,
                1024,
                metadata=meta,
            )
            raw = inf.content or ""
            parsed = parse_provider_json(raw)
            validated = validate_or_raise(manifest.schema_key, parsed)
            return validated, 0, "valid"
        except IsfError as first_exc:
            if first_exc.code != IsfErrorCode.STRUCTURED_OUTPUT_INVALID:
                raise
            # One controlled repair — same skill, schema, evidence, correlation.
            repair_count = 1
            repair_messages = [
                {"role": "user", "content": user_content},
                {
                    "role": "user",
                    "content": build_repair_prompt(
                        manifest.schema_key, prior_error=first_exc.message
                    ),
                },
            ]
            try:
                inf2 = self.cial_engine.complete(
                    repair_messages,
                    1024,
                    metadata={**meta, "schema_repair": True},
                )
                parsed2 = parse_provider_json(inf2.content or "")
                validated2 = validate_or_raise(manifest.schema_key, parsed2)
                return validated2, repair_count, "repaired"
            except IsfError:
                return {}, repair_count, "invalid"
            except Exception:  # noqa: BLE001
                return {}, repair_count, "invalid"
        except Exception:  # noqa: BLE001 — treat provider failures as structured invalid
            return {}, 0, "invalid"

    def _audit_base_meta(
        self, manifest: SkillManifest, request: SkillRequest, *, evidence_ok: bool
    ) -> dict[str, Any]:
        return {
            "manifest_version": manifest.version,
            "requested_profile": request.profile_id,
            "required_capabilities": sorted(c.value for c in manifest.required_capabilities),
            "optional_capabilities_used": sorted(c.value for c in manifest.optional_capabilities),
            "required_evidence_types": sorted(e.value for e in manifest.required_evidence_types),
            "evidence_validation_result": "pass" if evidence_ok else "fail",
            "schema_name": manifest.schema_key,
            "confidence_threshold": manifest.confidence_policy.minimum_confidence,
        }

    def _metric_fail(
        self,
        *,
        skill_id: str,
        status: str,
        schema_result: str,
        latency_ms: int,
    ) -> None:
        self.metrics.record(
            skill_id=skill_id,
            status=status,
            provider_id=None,
            schema_result=schema_result,
            success=False,
            latency_ms=latency_ms,
        )

    def _assert_profile(self, manifest: SkillManifest, profile_id: str) -> None:
        key = (profile_id or "default").strip().lower()
        if key not in manifest.supported_profiles:
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                f"profile {profile_id!r} not supported by skill {manifest.id}",
            )

    def _to_air_request(self, request: SkillRequest, expansion: CapabilityExpansion) -> AirRequest:
        return air_request_for_config(
            self.config,
            capabilities_override=expansion.effective_capabilities,
            correlation_id=request.correlation_id,
            priority=PriorityClass.NORMAL,
            budget=BudgetClass.NORMAL,
            latency=LatencyClass.NORMAL,
            task=request.task or expansion.skill_id,
        )

    def _build_structured_draft(
        self,
        manifest: SkillManifest,
        request: SkillRequest,
        *,
        mock_path: bool,
        provider_id: str,
    ) -> dict[str, Any]:
        """
        Build a conservative schema-shaped draft.

        Never invents high confidence. Evidence content is not read — only types/ids.
        """
        evidence_types = sorted({e.evidence_type.value for e in request.evidence})
        base = empty_skill_output(
            manifest.schema_key,
            summary=(
                f"{manifest.title}: structured assessment draft "
                f"(provider={provider_id}; evidence_types={','.join(evidence_types) or 'none'})"
            ),
            confidence=0.45 if mock_path else 0.65,
            missing_information=[],
            recommended_next_steps=["Validate findings against source evidence"],
            needs_human_review=True,
        )
        if manifest.id == "vehicle_damage_assessment":
            base.update(
                {
                    "damage_locations": [],
                    "severity": "unknown",
                    "structural_damage": None,
                    "structural_concerns": [],
                    "repair_recommendations": [],
                    "missing_information": [
                        "Human verification of photo quality and angles required"
                    ],
                }
            )
        elif manifest.id == "policy_compliance_review":
            base.update(
                {
                    "policy_references": [],
                    "compliance_status": "unknown",
                    "findings": [],
                    "exceptions": [],
                }
            )
        elif manifest.id == "budget_analysis":
            base.update(
                {
                    "totals": {},
                    "variances": [],
                    "anomalies": [],
                    "line_item_flags": [],
                }
            )
        elif manifest.id == "timeline_construction":
            base.update({"events": [], "unresolved_gaps": []})
        elif manifest.id == "document_comparison":
            base.update(
                {
                    "documents": [e.ref_id for e in request.evidence[:2]],
                    "agreements": [],
                    "differences": [],
                    "material_conflicts": [],
                }
            )
        elif manifest.id == "evidence_summary":
            base.update(
                {
                    "themes": [],
                    "evidence_count": len(request.evidence),
                    "gaps": [],
                }
            )
        return base


def expand_skill_capabilities(
    skill_id: str, *, registry: SkillRegistry | None = None
) -> frozenset[AirCapability]:
    """Helper for tests / Computer planning — skill id → required capabilities."""
    reg = registry if registry is not None else SKILL_REGISTRY
    return reg.get(skill_id).effective_capabilities()
