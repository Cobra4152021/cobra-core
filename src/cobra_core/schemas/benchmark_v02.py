"""CobraBench v0.2 case schema (release-candidate capable)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cobra_core.schemas.benchmark import (
    CitationRequirements,
    ExpectedBehavior,
    HumanScoredDimension,
    ObjectiveCheck,
    ProhibitedBehavior,
    ScoringRubricRef,
    SupportingSource,
)
from cobra_core.schemas.categories import BenchmarkCategory


class MaterialEvidenceSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_evidence_ids: list[str] = Field(default_factory=list)
    optional_evidence_ids: list[str] = Field(default_factory=list)
    contrary_evidence_ids: list[str] = Field(default_factory=list)
    minimum_source_diversity: Annotated[int, Field(ge=0)] = 0
    claim_level_citation_required: bool = True


class FormatExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    semantic_fields: list[str] = Field(default_factory=list)
    exact_fields: list[str] = Field(default_factory=list)
    parser_mode: Literal["strict", "tolerant", "both"] = "both"
    machine_interoperability_required: bool = False
    field_order_matters: bool = False
    extra_prose_prohibited: bool = False
    tolerant_recovery_allowed: bool = True


class ContradictionExpectations(BaseModel):
    model_config = ConfigDict(extra="forbid")

    subdimensions: list[str] = Field(
        default_factory=lambda: [
            "detection",
            "localization",
            "classification",
            "explanation",
            "numerical_comparison",
            "timeline_comparison",
            "preservation_of_competing_accounts",
            "avoidance_of_invented_reconciliation",
            "resolution_evidence_recommendation",
            "confidence_calibration",
        ]
    )
    expected_conflict_markers: list[str] = Field(default_factory=list)
    is_apparent_only: bool = False
    expects_shallow_explanation_trap: bool = False
    expects_over_eager_contradiction_trap: bool = False


class OutputBudgetExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    runtime_profile_id: str | None = None
    required_sections: list[str] = Field(default_factory=list)
    early_stop_expectation: Literal[
        "natural_or_complete",
        "may_be_short",
        "expect_full_sections",
        "unspecified",
    ] = "unspecified"


class EvaluatorVersionPin(BaseModel):
    model_config = ConfigDict(extra="forbid")

    unsupported_claims: str | None = None
    format_compliance: str | None = None
    citations: str | None = None
    contradictions: str | None = None
    output_budget_telemetry: str | None = None


class HumanReviewRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    reviewer_status: Literal["approved", "revised_then_approved", "rejected"]
    single_reviewer: bool = True
    issues_found: list[str] = Field(default_factory=list)
    corrections_made: list[str] = Field(default_factory=list)
    unresolved_ambiguity: list[str] = Field(default_factory=list)
    approval_status: Literal["approved", "blocked"] = "approved"
    clarity: Annotated[int, Field(ge=1, le=5)] = 4
    sufficiency_of_evidence: Annotated[int, Field(ge=1, le=5)] = 4
    fairness: Annotated[int, Field(ge=1, le=5)] = 4
    scoring_clarity: Annotated[int, Field(ge=1, le=5)] = 4
    investigation_relevance: Annotated[int, Field(ge=1, le=5)] = 4

    @model_validator(mode="after")
    def block_unresolved(self) -> HumanReviewRecord:
        if self.unresolved_ambiguity and self.approval_status == "approved":
            raise ValueError("Cannot approve case with unresolved_ambiguity")
        if self.approval_status == "blocked" and self.reviewer_status == "approved":
            raise ValueError("Blocked cases cannot have reviewer_status=approved")
        return self


class ContaminationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_origin: str
    authoring_method: Literal[
        "synthetic_authored", "public_domain_transform", "permissive_transform"
    ]
    licensing_status: str
    synthetic: bool = True
    transformed_from_public_material: bool = False
    pretraining_exposure_risk: Literal["low", "medium", "high"] = "low"
    answer_leakage_risk: Literal["low", "medium", "high"] = "low"
    training_set_exclusion_status: str = "exclude_from_future_training_corpora"


class ReferenceBehavior(BaseModel):
    model_config = ConfigDict(extra="forbid")

    required_findings: list[str] = Field(default_factory=list)
    acceptable_alternatives: list[str] = Field(default_factory=list)
    material_omissions: list[str] = Field(default_factory=list)
    prohibited_claims: list[str] = Field(default_factory=list)
    evidence_dependencies: list[str] = Field(default_factory=list)
    acceptable_uncertainty: list[str] = Field(default_factory=list)
    unacceptable_certainty: list[str] = Field(default_factory=list)
    required_citations: list[str] = Field(default_factory=list)
    optional_citations: list[str] = Field(default_factory=list)


class BenchmarkCaseV02(BaseModel):
    """CobraBench v0.2 case model (draft or release candidate)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: Annotated[
        str,
        Field(
            min_length=1,
            pattern=r"^(cb2-\d{3}-[a-z0-9-]+|draft-\d{3}-[a-z0-9-]+)$",
        ),
    ]
    version: Annotated[str, Field(min_length=1)]
    status: Literal["draft", "non_official", "release_candidate"] = "draft"
    official_release: bool = False
    scored: bool = False
    frozen: bool = False
    part_of_cobrabench_v01: bool = False
    category: BenchmarkCategory
    title: Annotated[str, Field(min_length=1)]
    # Draft examples may omit difficulty; RC cases must set 1–4 explicitly.
    difficulty_level: Annotated[int, Field(ge=1, le=5)] = 2
    system_prompt: Annotated[str, Field(min_length=1)]
    user_prompt: Annotated[str, Field(min_length=1)]
    supporting_sources: list[SupportingSource] = Field(default_factory=list)
    expected_behaviors: list[ExpectedBehavior] = Field(default_factory=list)
    prohibited_behaviors: list[ProhibitedBehavior] = Field(default_factory=list)
    scoring_rubric: ScoringRubricRef
    sensitivity: str = "public_synthetic"
    tags: list[str] = Field(default_factory=list)
    objective_checks: list[ObjectiveCheck] = Field(default_factory=list)
    human_scored_dimensions: list[HumanScoredDimension] = Field(default_factory=list)
    citation_requirements: CitationRequirements | None = None
    material_evidence: MaterialEvidenceSpec | None = None
    format_expectations: FormatExpectations | None = None
    contradiction_expectations: ContradictionExpectations | None = None
    output_budget: OutputBudgetExpectation | None = None
    prompt_template_id: str | None = None
    prompt_template_version: str | None = None
    evaluator_versions: EvaluatorVersionPin | None = None
    uncertainty_requirements: list[str] = Field(default_factory=list)
    refusal_expectations: str | None = None
    reference_behavior: ReferenceBehavior | None = None
    human_review: HumanReviewRecord | None = None
    contamination: ContaminationRecord | None = None
    known_ambiguity_notes: str | None = None
    notes: str | None = None

    @field_validator("part_of_cobrabench_v01")
    @classmethod
    def never_v01(cls, value: bool) -> bool:
        if value:
            raise ValueError("v0.2 cases must set part_of_cobrabench_v01=false")
        return value

    @model_validator(mode="after")
    def rc_requires_review(self) -> BenchmarkCaseV02:
        if self.status == "release_candidate":
            if self.human_review is None or self.human_review.approval_status != "approved":
                raise ValueError("release_candidate cases require approved human_review")
            if self.contamination is None:
                raise ValueError("release_candidate cases require contamination record")
            if not self.expected_behaviors:
                raise ValueError("release_candidate cases require expected_behaviors")
        return self
