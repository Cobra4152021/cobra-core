"""Weakness taxonomy enums and case-level analysis schema."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class WeaknessClass(StrEnum):
    """Phase 2E weakness cause taxonomy (Part 3)."""

    MODEL_CAPABILITY = "M"
    RUNTIME_QUANTIZATION = "R"
    PROMPT_TEMPLATE = "P"
    OUTPUT_LENGTH = "L"
    BENCHMARK_DEFECT = "B"
    SCORING_PARSER = "S"
    HUMAN_REVIEW = "H"
    UNKNOWN = "U"


class ConfidenceLevel(StrEnum):
    """Confidence in primary/contributing class assignment."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class DiagnosticPriority(StrEnum):
    """Priority for controlled diagnostic reruns."""

    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CaseWeaknessAnalysis(BaseModel):
    """Per-case static weakness analysis record (Phase 2E Part 4)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_id: Annotated[str, Field(min_length=1)]
    category: Annotated[str, Field(min_length=1)]
    baseline_score: Annotated[float, Field(ge=0.0, le=1.0)]
    rule_failures: list[str] = Field(default_factory=list)
    human_findings: Annotated[str, Field(min_length=1)]
    output_length_chars: Annotated[int, Field(ge=0)]
    finish_reason: str | None = None
    input_tokens: Annotated[int, Field(ge=0)] = 0
    output_tokens: Annotated[int, Field(ge=0)] = 0
    latency_ms: float | None = None
    citation_metrics: dict[str, Any] = Field(default_factory=dict)
    hallucination_severity_human: str | None = None
    hallucination_severity_automated: str | None = None
    observed_weakness: Annotated[str, Field(min_length=1)]
    primary_weakness_class: WeaknessClass | None = None
    contributing_classes: list[WeaknessClass] = Field(default_factory=list)
    confidence: ConfidenceLevel
    diagnostic_priority: DiagnosticPriority
    rerun_justified: bool = False
    rerun_reason: str | None = None
    proposed_controlled_variable: str | None = None
    evidence: list[str] = Field(default_factory=list)
    diagnostic_test: str | None = None
