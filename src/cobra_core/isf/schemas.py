"""Structured output schemas for built-in investigation skills."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SkillOutputBase(BaseModel):
    """Common fields every skill output must carry."""

    summary: str = Field(default="", description="Concise investigation summary")
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    missing_information: list[str] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)
    needs_human_review: bool = False


class VehicleDamageAssessmentOutput(SkillOutputBase):
    damage_locations: list[str] = Field(default_factory=list)
    severity: Literal["unknown", "minor", "moderate", "severe", "total"] = "unknown"
    structural_damage: bool | None = None
    structural_concerns: list[str] = Field(default_factory=list)
    repair_recommendations: list[str] = Field(default_factory=list)


class PolicyComplianceReviewOutput(SkillOutputBase):
    policy_references: list[str] = Field(default_factory=list)
    compliance_status: Literal["unknown", "compliant", "noncompliant", "partial"] = "unknown"
    findings: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)


class ContractAnalysisOutput(SkillOutputBase):
    parties: list[str] = Field(default_factory=list)
    key_terms: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class BudgetAnalysisOutput(SkillOutputBase):
    totals: dict[str, float] = Field(default_factory=dict)
    variances: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    line_item_flags: list[str] = Field(default_factory=list)


class EvidenceSummaryOutput(SkillOutputBase):
    themes: list[str] = Field(default_factory=list)
    evidence_count: int = 0
    gaps: list[str] = Field(default_factory=list)


class TimelineConstructionOutput(SkillOutputBase):
    events: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_gaps: list[str] = Field(default_factory=list)


class PatternDetectionOutput(SkillOutputBase):
    patterns: list[str] = Field(default_factory=list)
    supporting_signals: list[str] = Field(default_factory=list)
    false_positive_risks: list[str] = Field(default_factory=list)


class OpenSourceResearchOutput(SkillOutputBase):
    sources_considered: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class InterviewSummaryOutput(SkillOutputBase):
    participants: list[str] = Field(default_factory=list)
    key_statements: list[str] = Field(default_factory=list)
    inconsistencies: list[str] = Field(default_factory=list)


class DocumentComparisonOutput(SkillOutputBase):
    documents: list[str] = Field(default_factory=list)
    agreements: list[str] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    material_conflicts: list[str] = Field(default_factory=list)


SCHEMA_BY_SKILL_ID: dict[str, type[SkillOutputBase]] = {
    "vehicle_damage_assessment": VehicleDamageAssessmentOutput,
    "policy_compliance_review": PolicyComplianceReviewOutput,
    "contract_analysis": ContractAnalysisOutput,
    "budget_analysis": BudgetAnalysisOutput,
    "evidence_summary": EvidenceSummaryOutput,
    "timeline_construction": TimelineConstructionOutput,
    "pattern_detection": PatternDetectionOutput,
    "open_source_research": OpenSourceResearchOutput,
    "interview_summary": InterviewSummaryOutput,
    "document_comparison": DocumentComparisonOutput,
}


def validate_skill_output(skill_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate and normalize a structured skill payload."""
    model_cls = SCHEMA_BY_SKILL_ID.get(skill_id)
    if model_cls is None:
        raise ValueError(f"no output schema registered for skill: {skill_id!r}")
    return model_cls.model_validate(payload).model_dump(mode="json")


def empty_skill_output(skill_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a minimal valid structured output for a skill."""
    model_cls = SCHEMA_BY_SKILL_ID.get(skill_id)
    if model_cls is None:
        raise ValueError(f"no output schema registered for skill: {skill_id!r}")
    return model_cls(**overrides).model_dump(mode="json")
