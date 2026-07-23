"""Prospective CobraBench v0.2 case schema (draft — not an official release)."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

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


class BenchmarkCaseV02(BaseModel):
    """
    Prospective draft case model for CobraBench v0.2.

    Not an official release. Must not mutate v0.1 cases.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: Annotated[str, Field(min_length=1)]
    version: Annotated[str, Field(min_length=1)]
    status: Literal["draft", "non_official"] = "draft"
    official_release: bool = False
    scored: bool = False
    frozen: bool = False
    part_of_cobrabench_v01: bool = False
    category: BenchmarkCategory
    title: Annotated[str, Field(min_length=1)]
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
    notes: str | None = None
