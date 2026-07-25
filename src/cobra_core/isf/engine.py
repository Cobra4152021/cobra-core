"""
Investigation Skill Engine — expand skill → AIR → structured result.

Computer requests a skill id. ISF expands capabilities; AIR selects provider.
"""

from __future__ import annotations

from typing import Any

from cobra_core.air.bridge import air_request_for_config, build_adaptive_router
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.errors import AirRoutingError
from cobra_core.air.types import AirRequest, BudgetClass, LatencyClass, PriorityClass
from cobra_core.cial.config import CialConfig, load_cial_config
from cobra_core.cial.engine import CialEngine
from cobra_core.isf.audit import ISF_AUDIT, IsfAuditLog
from cobra_core.isf.confidence import ConfidenceDisposition
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import missing_required_evidence
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.registry import SKILL_REGISTRY, SkillRegistry
from cobra_core.isf.schemas import empty_skill_output, validate_skill_output
from cobra_core.isf.types import (
    CapabilityExpansion,
    SkillExecutionStatus,
    SkillRequest,
    SkillResult,
)


class SkillEngine:
    """Resolve skill manifests, expand capabilities, route via AIR, return typed results."""

    def __init__(
        self,
        *,
        registry: SkillRegistry | None = None,
        config: CialConfig | None = None,
        cial_engine: CialEngine | None = None,
        audit: IsfAuditLog | None = None,
    ) -> None:
        self.registry = registry if registry is not None else SKILL_REGISTRY
        self.config = config or load_cial_config()
        self.cial_engine = cial_engine
        self.audit = audit if audit is not None else ISF_AUDIT

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
        Full skill execution path (fail closed on missing evidence / routing).

        Does not store prompts. Structured output is always schema-validated.
        """
        try:
            manifest = self.registry.get(request.skill_id)
        except IsfError as exc:
            raise exc

        self._assert_profile(manifest, request.profile_id)

        missing = missing_required_evidence(manifest.required_evidence_types, request.evidence)
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
            )
            self.audit.record(result)
            return result

        expansion = self.expand(request)
        air_req = self._to_air_request(request, expansion)
        router = build_adaptive_router(self.config)
        try:
            decision = router.route(air_req)
        except AirRoutingError as exc:
            raise IsfError(
                IsfErrorCode.ROUTING_FAILED,
                f"AIR routing failed: {exc.air_code.value}",
            ) from exc

        mock_path = decision.provider_id == "mock"
        draft = self._build_structured_draft(
            manifest,
            request,
            mock_path=mock_path,
            provider_id=decision.provider_id,
        )

        # Optional inference — content used only as length/metadata, never as sole output.
        if self.cial_engine is not None and not mock_path:
            try:
                inf = self.cial_engine.complete(
                    [
                        {
                            "role": "user",
                            "content": (
                                f"Skill={manifest.id}. Return concise investigation notes only."
                            ),
                        }
                    ],
                    64,
                    metadata={"correlation_id": request.correlation_id, "skill_id": manifest.id},
                )
                draft.setdefault("metadata_provider_chars", len(inf.content or ""))
            except Exception:  # noqa: BLE001 — structured path must remain fail-closed safely
                draft["missing_information"] = list(
                    dict.fromkeys(
                        [*draft.get("missing_information", []), "provider_inference_unavailable"]
                    )
                )

        incomplete = bool(draft.get("missing_information")) or bool(missing)
        raw_conf = float(draft.get("confidence") or 0.0)
        conf = manifest.confidence_policy.clamp(
            raw_conf, incomplete_evidence=incomplete, mock_path=mock_path
        )
        disposition = manifest.confidence_policy.disposition(conf)
        needs_review = disposition == ConfidenceDisposition.NEEDS_HUMAN_REVIEW
        draft["confidence"] = conf
        draft["needs_human_review"] = needs_review
        if (
            needs_review
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
                IsfErrorCode.SCHEMA_VALIDATION_FAILED,
                "structured skill output failed schema validation",
            ) from exc

        status = (
            SkillExecutionStatus.NEEDS_HUMAN_REVIEW
            if needs_review
            else SkillExecutionStatus.COMPLETED
        )
        result = SkillResult(
            skill_id=manifest.id,
            skill_version=manifest.version,
            status=status,
            output=output,
            confidence=conf,
            confidence_disposition=disposition,
            expanded_capabilities=expansion.effective_capabilities,
            missing_evidence=(),
            selected_provider=decision.provider_id,
            selected_model=decision.model_id,
            route_reason=decision.reason,
            correlation_id=request.correlation_id,
            needs_human_review=needs_review,
            metadata={"policy_id": decision.policy_id},
        )
        self.audit.record(result)
        return result

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
        # Skill-specific conservative placeholders (typed, not free-form only).
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
