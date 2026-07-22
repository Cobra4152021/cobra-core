"""EvaluationRun — preserved record of a single model evaluation."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from cobra_core.schemas.categories import CATEGORY_WEIGHTS, BenchmarkCategory


class EvaluatorKind(StrEnum):
    """
    Distinct evaluation evidence types.

    These must remain separated. LLM-as-judge results are never
    treated as unquestionable ground truth.
    """

    OBJECTIVE = "objective"  # deterministic measurements (latency, tokens, regex, etc.)
    RULE_BASED = "rule_based"  # explicit programmatic checks against expected/prohibited behaviors
    HUMAN = "human"  # human evaluator judgments
    LLM_AS_JUDGE = "llm_as_judge"  # advisory only; require rationale and human review path


class InferenceSettings(BaseModel):
    """Exact inference parameters used for the run."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    temperature: Annotated[float, Field(ge=0.0, le=2.0)] = 0.0
    top_p: Annotated[float | None, Field(default=None, ge=0.0, le=1.0)] = None
    max_tokens: Annotated[int | None, Field(default=None, ge=1)] = None
    stop: list[str] | None = None
    seed: int | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class HardwareMetadata(BaseModel):
    """Hardware / runtime metadata for reproducibility notes."""

    model_config = ConfigDict(extra="allow", str_strip_whitespace=True)

    device: str | None = None
    accelerator: str | None = None
    runtime: str | None = None
    os_name: str | None = None
    notes: str | None = None


class EvaluatorScore(BaseModel):
    """A single score contribution with rationale and evaluator provenance."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    category: BenchmarkCategory
    kind: EvaluatorKind
    score: Annotated[float, Field(ge=0.0, le=1.0)]
    rationale: Annotated[str, Field(min_length=1)]
    evaluator_version: Annotated[str, Field(min_length=1)]
    confidence: Annotated[float | None, Field(default=None, ge=0.0, le=1.0)] = None
    is_advisory: bool = False

    @model_validator(mode="after")
    def llm_judge_is_advisory(self) -> EvaluatorScore:
        if self.kind == EvaluatorKind.LLM_AS_JUDGE:
            object.__setattr__(self, "is_advisory", True)
        return self


class ScoreBreakdown(BaseModel):
    """
    Category-level score detail.

    Never discard per-category scores in favor of only an overall number.
    """

    model_config = ConfigDict(extra="forbid")

    by_category: dict[BenchmarkCategory, float]
    weights_applied: dict[BenchmarkCategory, float] = Field(
        default_factory=lambda: dict(CATEGORY_WEIGHTS)
    )
    notes: str | None = None

    @field_validator("by_category")
    @classmethod
    def scores_in_unit_interval(
        cls, value: dict[BenchmarkCategory, float]
    ) -> dict[BenchmarkCategory, float]:
        for category, score in value.items():
            if score < 0.0 or score > 1.0:
                raise ValueError(f"score for {category} must be in [0, 1], got {score}")
        return value

    def weighted_overall(self) -> float | None:
        """
        Compute a weighted overall score when all weighted categories are present.

        Returns None if the breakdown is incomplete — callers must not invent a score.
        """
        total = 0.0
        weight_sum = 0.0
        for category, weight in self.weights_applied.items():
            if category not in self.by_category:
                return None
            total += self.by_category[category] * weight
            weight_sum += weight
        if weight_sum <= 0:
            return None
        return total / weight_sum


class EvaluationRun(BaseModel):
    """
    Full evaluation preservation record.

    Every run must retain: exact prompt, model revision, inference parameters,
    raw model output location, evaluator version(s), and scoring rationale.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    run_id: Annotated[str, Field(min_length=1, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9._-]*$")]
    timestamp: datetime
    model_manifest_ref: Annotated[
        str,
        Field(
            min_length=1,
            description="Path or ID referencing a ModelManifest (not the weights)",
        ),
    ]
    model_revision: Annotated[
        str,
        Field(min_length=1, description="Exact model revision evaluated"),
    ]
    benchmark_version: Annotated[str, Field(min_length=1)]
    case_id: Annotated[str, Field(min_length=1)]
    system_prompt: Annotated[str, Field(min_length=1)]
    user_prompt: Annotated[str, Field(min_length=1)]
    inference_settings: InferenceSettings
    hardware: HardwareMetadata = Field(default_factory=HardwareMetadata)
    raw_response_location: Annotated[
        str,
        Field(min_length=1, description="Path to raw model output artifact"),
    ]
    latency_ms: Annotated[float | None, Field(default=None, ge=0.0)] = None
    prompt_tokens: Annotated[int | None, Field(default=None, ge=0)] = None
    completion_tokens: Annotated[int | None, Field(default=None, ge=0)] = None
    cost_usd: Annotated[float | None, Field(default=None, ge=0.0)] = None
    deterministic_seed: int | None = None
    evaluator_scores: Annotated[list[EvaluatorScore], Field(min_length=1)]
    score_breakdown: ScoreBreakdown
    overall_score: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            le=1.0,
            description="Weighted overall; must not replace category detail",
        ),
    ] = None
    evaluator_version: Annotated[
        str,
        Field(min_length=1, description="Primary evaluator bundle version for this run"),
    ]
    notes: str | None = None

    @model_validator(mode="after")
    def overall_matches_breakdown_when_present(self) -> EvaluationRun:
        computed = self.score_breakdown.weighted_overall()
        if (
            self.overall_score is not None
            and computed is not None
            and abs(self.overall_score - computed) > 1e-6
        ):
            raise ValueError(
                "overall_score must match score_breakdown.weighted_overall() "
                f"(got {self.overall_score}, computed {computed})"
            )
        return self
