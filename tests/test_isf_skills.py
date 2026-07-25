"""KC-024 Investigation Skills Framework tests."""

from __future__ import annotations

import pytest

from cobra_core.air.audit import AIR_AUDIT
from cobra_core.air.capabilities import AirCapability
from cobra_core.air.metrics import AIR_METRICS
from cobra_core.cial.config import CialConfig
from cobra_core.cial.types import RoutingPolicy
from cobra_core.isf.audit import ISF_AUDIT
from cobra_core.isf.confidence import ConfidenceDisposition, ConfidencePolicy
from cobra_core.isf.engine import SkillEngine, expand_skill_capabilities
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.registry import SkillRegistry
from cobra_core.isf.schemas import (
    VehicleDamageAssessmentOutput,
    empty_skill_output,
    validate_skill_output,
)
from cobra_core.isf.skills import builtin_skill_manifests, register_builtin_skills
from cobra_core.isf.skills.vehicle_damage import build_vehicle_damage_output
from cobra_core.isf.types import SkillExecutionStatus, SkillRequest
from cobra_core.protocol_v1.constants import DEFAULT_MODEL


@pytest.fixture(autouse=True)
def _reset_audits() -> None:
    ISF_AUDIT.clear()
    AIR_AUDIT.clear()
    AIR_METRICS.reset()
    yield
    ISF_AUDIT.clear()


def _cfg(**overrides: object) -> CialConfig:
    base = dict(
        enabled=True,
        active_profile="default",
        routing_policy=RoutingPolicy.DEFAULT,
        app_env="staging",
        live_provider_enabled=False,
        mock_model=DEFAULT_MODEL,
    )
    base.update(overrides)
    return CialConfig(**base)  # type: ignore[arg-type]


# --- Registry / manifests -------------------------------------------------


def test_builtin_skills_registered() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    assert len(reg) == 10
    expected = {
        "vehicle_damage_assessment",
        "policy_compliance_review",
        "contract_analysis",
        "budget_analysis",
        "evidence_summary",
        "timeline_construction",
        "pattern_detection",
        "open_source_research",
        "interview_summary",
        "document_comparison",
    }
    assert set(reg.ids()) == expected


def test_manifest_requires_capabilities_and_schema() -> None:
    with pytest.raises(IsfError) as exc:
        SkillManifest(
            id="broken",
            title="Broken",
            version="1.0.0",
            description="x",
            required_capabilities=frozenset(),
        )
    assert exc.value.code == IsfErrorCode.MANIFEST_INVALID


def test_unknown_skill() -> None:
    engine = SkillEngine(registry=SkillRegistry(), config=_cfg())
    with pytest.raises(IsfError) as exc:
        engine.execute(SkillRequest(skill_id="not_a_skill"))
    assert exc.value.code == IsfErrorCode.SKILL_NOT_FOUND


# --- Capability expansion -------------------------------------------------


def test_vehicle_damage_expands_to_vision_reasoning_structured() -> None:
    caps = expand_skill_capabilities("vehicle_damage_assessment")
    assert AirCapability.VISION in caps
    assert AirCapability.REASONING in caps
    assert AirCapability.STRUCTURED_OUTPUT in caps
    # Computer must not pass providers
    assert "openai" not in {c.value for c in caps}


def test_evidence_summary_expansion() -> None:
    caps = expand_skill_capabilities("evidence_summary")
    assert AirCapability.SUMMARIZATION in caps


# --- Schema validation ----------------------------------------------------


def test_vehicle_damage_schema_validation() -> None:
    payload = build_vehicle_damage_output(
        summary="Rear bumper scuff",
        damage_locations=["rear_bumper"],
        severity="minor",
        structural_damage=False,
        structural_concerns=[],
        repair_recommendations=["Inspect bumper cover"],
        confidence=0.4,
        missing_information=["Additional angle photos"],
        recommended_next_steps=["Human photo review"],
        needs_human_review=True,
    )
    assert payload["severity"] == "minor"
    assert "summary" in payload
    model = VehicleDamageAssessmentOutput.model_validate(payload)
    assert model.confidence == 0.4


def test_invalid_schema_rejected() -> None:
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        validate_skill_output(
            "vehicle_damage_assessment",
            {"summary": "x", "confidence": 2.5},  # out of range
        )


# --- Missing evidence -----------------------------------------------------


def test_missing_required_evidence_typed() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(registry=reg, config=_cfg())
    result = engine.execute(
        SkillRequest(
            skill_id="vehicle_damage_assessment",
            evidence=(),
            correlation_id="isf_miss_1",
        )
    )
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
    assert EvidenceType.VEHICLE_PHOTOS in result.missing_evidence
    assert result.output["error"]["code"] == "missing_required_evidence"
    assert result.needs_human_review is True
    assert ISF_AUDIT.recent()[-1]["missing_evidence"] == ["vehicle_photos"]


def test_budget_requires_spreadsheet() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(registry=reg, config=_cfg())
    result = engine.execute(
        SkillRequest(
            skill_id="budget_analysis",
            evidence=(EvidenceRef(EvidenceType.CASE_NOTES, "n1"),),
        )
    )
    assert result.status == SkillExecutionStatus.MISSING_REQUIRED_EVIDENCE
    assert EvidenceType.BUDGET_SPREADSHEET in result.missing_evidence


# --- Confidence -----------------------------------------------------------


def test_confidence_policy_clamp_and_disposition() -> None:
    policy = ConfidencePolicy(minimum_confidence=0.75, mock_confidence_cap=0.5)
    clamped = policy.clamp(0.9, incomplete_evidence=False, mock_path=True)
    assert clamped <= 0.5
    assert policy.disposition(clamped) == ConfidenceDisposition.NEEDS_HUMAN_REVIEW
    assert policy.disposition(0.8) == ConfidenceDisposition.ACCEPTABLE


def test_execution_confidence_forces_human_review_on_mock() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(registry=reg, config=_cfg())
    result = engine.execute(
        SkillRequest(
            skill_id="evidence_summary",
            evidence=(EvidenceRef(EvidenceType.EVIDENCE_BUNDLE, "bundle_1"),),
            correlation_id="isf_conf_1",
        )
    )
    assert result.selected_provider == "mock"
    assert result.confidence <= 0.5
    assert result.needs_human_review is True
    assert result.status == SkillExecutionStatus.NEEDS_HUMAN_REVIEW
    assert "summary" in result.output
    assert isinstance(result.output, dict)


# --- Vehicle damage + AIR -------------------------------------------------


def test_vehicle_damage_routes_openai_when_live_open() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    cfg = _cfg(
        active_profile="research",
        live_provider_enabled=True,
        openai_api_key="k",
        openai_model="gpt-5.4-mini",
    )
    assert cfg.can_use_live_provider
    engine = SkillEngine(registry=reg, config=cfg)
    result = engine.execute(
        SkillRequest(
            skill_id="vehicle_damage_assessment",
            evidence=(EvidenceRef(EvidenceType.VEHICLE_PHOTOS, "photo_1"),),
            profile_id="research",
            correlation_id="isf_vda_live",
        )
    )
    assert result.selected_provider == "openai"
    assert result.selected_model == "gpt-5.4-mini"
    assert result.output["severity"] in {"unknown", "minor", "moderate", "severe", "total"}
    audit = ISF_AUDIT.recent()[-1]
    assert audit["skill"] == "vehicle_damage_assessment"
    assert "vision" in audit["expanded_capabilities"]
    assert "prompt" not in audit


def test_vehicle_damage_fail_closed_without_vision_provider() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(registry=reg, config=_cfg())
    with pytest.raises(IsfError) as exc:
        engine.execute(
            SkillRequest(
                skill_id="vehicle_damage_assessment",
                evidence=(EvidenceRef(EvidenceType.VEHICLE_PHOTOS, "photo_1"),),
            )
        )
    assert exc.value.code == IsfErrorCode.ROUTING_FAILED


# --- Audit ----------------------------------------------------------------


def test_audit_records_skill_fields_not_prompts() -> None:
    reg = SkillRegistry()
    register_builtin_skills(reg)
    engine = SkillEngine(registry=reg, config=_cfg())
    engine.execute(
        SkillRequest(
            skill_id="interview_summary",
            evidence=(EvidenceRef(EvidenceType.INTERVIEW_TRANSCRIPT, "t1"),),
            correlation_id="isf_audit_1",
        )
    )
    entry = ISF_AUDIT.recent()[-1]
    for key in (
        "skill",
        "skill_version",
        "expanded_capabilities",
        "confidence_score",
        "missing_evidence",
    ):
        assert key in entry
    assert entry["correlation_id"] == "isf_audit_1"
    assert "messages" not in entry
    assert "prompt" not in entry


# --- Structured outputs for all builtins ----------------------------------


@pytest.mark.parametrize("manifest", builtin_skill_manifests())
def test_all_builtin_schemas_have_empty_output(manifest: SkillManifest) -> None:
    out = empty_skill_output(manifest.schema_key)
    assert "summary" in out
    assert "confidence" in out
    validate_skill_output(manifest.schema_key, out)
