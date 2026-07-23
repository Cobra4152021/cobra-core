"""Types for unsupported-claim evaluators."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class ClaimClass(StrEnum):
    FACTUAL_CLAIM = "factual_claim"
    EVIDENCE_PARAPHRASE = "evidence_paraphrase"
    EXPLICITLY_LABELED_INFERENCE = "explicitly_labeled_inference"
    RECOMMENDATION = "recommendation"
    QUESTION = "question"
    UNCERTAINTY_STATEMENT = "uncertainty_statement"
    STRUCTURAL_TEXT = "structural_text"
    HEADING = "heading"
    CONNECTIVE_LANGUAGE = "connective_language"
    INSTRUCTION_REPETITION = "instruction_repetition"
    QUOTED_SUPPLIED_EVIDENCE = "quoted_supplied_evidence"
    UNSUPPORTED_CANDIDATE = "unsupported_candidate"
    UNKNOWN = "unknown"


class SupportState(StrEnum):
    DIRECTLY_SUPPORTED = "directly_supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    SUPPORTED_BY_MULTIPLE = "supported_by_multiple_evidence_items"
    REASONABLE_LABELED_INFERENCE = "reasonable_labeled_inference"
    OVERSTATES_EVIDENCE = "overstates_evidence"
    UNSUPPORTED = "unsupported"
    CONTRADICTED_BY_EVIDENCE = "contradicted_by_evidence"
    CANNOT_DETERMINE = "cannot_determine"
    NOT_APPLICABLE = "not_applicable"


# Classes that must not enter support analysis as unsupported claims.
EXCLUDED_FROM_SUPPORT_ANALYSIS = frozenset(
    {
        ClaimClass.STRUCTURAL_TEXT,
        ClaimClass.HEADING,
        ClaimClass.CONNECTIVE_LANGUAGE,
        ClaimClass.INSTRUCTION_REPETITION,
        ClaimClass.RECOMMENDATION,
        ClaimClass.QUESTION,
        ClaimClass.QUOTED_SUPPLIED_EVIDENCE,
    }
)


class ClaimSpanResult(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    span_id: Annotated[str, Field(min_length=1)]
    text: Annotated[str, Field(min_length=1)]
    claim_class: ClaimClass
    support_state: SupportState
    cited_keys: list[str] = Field(default_factory=list)
    linked_evidence_ids: list[str] = Field(default_factory=list)
    enters_support_analysis: bool
    flagged_as_unsupported: bool = False
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    rationale: Annotated[str, Field(min_length=1)]
    rule_ids: list[str] = Field(default_factory=list)


class UnsupportedClaimEvaluation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = "unsupported_claims"
    evaluator_version: str
    spans: list[ClaimSpanResult]
    unsupported_flag_count: int
    analyzed_claim_count: int
    uncertain_count: int
    notes: str | None = None
