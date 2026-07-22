"""BenchmarkCase — CobraBench case definition schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from cobra_core.schemas.categories import BenchmarkCategory


class SensitivityLevel(StrEnum):
    """Content sensitivity for synthetic / public lab cases."""

    PUBLIC_SYNTHETIC = "public_synthetic"
    INTERNAL_NONSENSITIVE = "internal_nonsensitive"
    RESTRICTED = "restricted"


class SupportingSource(BaseModel):
    """A source the model should ground against for this case."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    source_id: Annotated[str, Field(min_length=1)]
    title: Annotated[str, Field(min_length=1)]
    content: Annotated[
        str, Field(min_length=1, description="Full source text provided to the model")
    ]
    citation_key: Annotated[
        str,
        Field(min_length=1, description="Stable key expected in citations, e.g. SRC-A"),
    ]


class ExpectedBehavior(BaseModel):
    """Observable behavior the response should exhibit."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    behavior_id: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    required: bool = True


class ProhibitedBehavior(BaseModel):
    """Behavior that should not appear in a high-quality response."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    behavior_id: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]


class ScoringRubricRef(BaseModel):
    """Reference to a rubric plus optional case-local notes."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    rubric_id: Annotated[str, Field(min_length=1)]
    rubric_version: Annotated[str, Field(min_length=1)]
    notes: str | None = None


class ObjectiveCheckType(StrEnum):
    """Automated check types for objective scoring."""

    CONTAINS_ANY = "contains_any"
    CONTAINS_ALL = "contains_all"
    REGEX = "regex"
    JSON_PARSE = "json_parse"
    CITATION_KEYS_VALID = "citation_keys_valid"
    EXACT_MATCH_OPTIONAL = "exact_match_optional"


class ObjectiveCheck(BaseModel):
    """Rule-based check applied to model output."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    check_id: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    check_type: ObjectiveCheckType


class HumanScoredDimension(BaseModel):
    """Dimension evaluated by a human or advisory LLM judge."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    dimension_id: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]


class CitationRequirements(BaseModel):
    """Citation discipline expectations for a case."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    required: bool
    allowed_keys: list[str] = Field(default_factory=list)
    allow_uncited_inference: bool = False


class BenchmarkCase(BaseModel):
    """
    A single CobraBench evaluation case.

    Cases in this repository must be synthetic / public-safe.
    Do not commit private evidence or active-case material.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: Annotated[str, Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9._-]*$")]
    version: Annotated[str, Field(min_length=1)]
    category: BenchmarkCategory
    title: Annotated[str, Field(min_length=1)]
    system_prompt: Annotated[str, Field(min_length=1)]
    user_prompt: Annotated[str, Field(min_length=1)]
    supporting_sources: list[SupportingSource] = Field(default_factory=list)
    expected_behaviors: Annotated[list[ExpectedBehavior], Field(min_length=1)]
    prohibited_behaviors: list[ProhibitedBehavior] = Field(default_factory=list)
    scoring_rubric: ScoringRubricRef
    sensitivity: SensitivityLevel = SensitivityLevel.PUBLIC_SYNTHETIC
    tags: list[str] = Field(default_factory=list)
    objective_checks: list[ObjectiveCheck] = Field(default_factory=list)
    human_scored_dimensions: list[HumanScoredDimension] = Field(default_factory=list)
    citation_requirements: CitationRequirements | None = None
    uncertainty_expectations: str | None = None
    refusal_expectations: str | None = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, value: list[str]) -> list[str]:
        cleaned = [tag.strip().lower() for tag in value if tag.strip()]
        return sorted(set(cleaned))
