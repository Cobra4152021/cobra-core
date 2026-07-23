"""Output-budget and early-stop telemetry (Phase 2F)."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

EVALUATOR_VERSION = "1.0.0"


class CompletionClass(StrEnum):
    LIKELY_NATURAL_COMPLETION = "likely_natural_completion"
    LIKELY_BUDGET_EXHAUSTION = "likely_budget_exhaustion"
    STOPPED_BEFORE_REQUIRED_SECTIONS = "stopped_before_required_sections"
    STOPPED_AFTER_CONCLUSION = "stopped_after_conclusion"
    UNKNOWN = "unknown"


class OutputBudgetTelemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = "output_budget_telemetry"
    evaluator_version: str = EVALUATOR_VERSION
    requested_max_output_tokens: int
    actual_output_tokens: int
    finish_reason: str | None
    end_of_sequence_detected: bool
    percentage_of_token_budget_used: Annotated[float, Field(ge=0.0)]
    required_section_completion: Annotated[float, Field(ge=0.0, le=1.0)]
    final_sentence_complete: bool
    output_stopped_after_conclusion: bool
    output_stopped_before_required_sections: bool
    completion_class: CompletionClass
    completion_confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    rationale: str


_CONCLUSION = re.compile(
    r"\b(in conclusion|summary|overall|final(?:ly)?|no further)\b",
    re.IGNORECASE,
)


def classify_output_budget(
    *,
    response: str,
    requested_max_output_tokens: int,
    actual_output_tokens: int,
    finish_reason: str | None,
    required_sections: list[str] | None = None,
) -> OutputBudgetTelemetry:
    """
    Diagnose truncation versus natural short completion.

    Short + completed/EOS is not automatically truncation.
    Budget exhaustion requires high budget utilization and/or length finish reason.
    """
    if requested_max_output_tokens <= 0:
        raise ValueError("requested_max_output_tokens must be positive")

    pct = (actual_output_tokens / requested_max_output_tokens) * 100.0
    eos = (finish_reason or "").lower() in {"completed", "eos", "stop", "end_of_sequence"}
    length_stop = (finish_reason or "").lower() in {"length", "max_tokens", "max_new_tokens"}

    sections = required_sections or []
    lower = response.lower()
    present = sum(1 for s in sections if s.lower() in lower)
    section_completion = present / len(sections) if sections else 1.0

    stripped = response.rstrip()
    final_complete = bool(stripped) and stripped[-1] in '.!?"'
    after_conclusion = bool(_CONCLUSION.search(response[-240:] if response else ""))
    before_required = bool(sections) and section_completion < 1.0

    completion = CompletionClass.UNKNOWN
    confidence = 0.4
    rationale_parts: list[str] = []

    if length_stop or pct >= 98.0:
        completion = CompletionClass.LIKELY_BUDGET_EXHAUSTION
        confidence = 0.85
        rationale_parts.append("finish_reason or budget utilization indicates exhaustion")
    elif before_required and pct < 50.0 and eos:
        completion = CompletionClass.STOPPED_BEFORE_REQUIRED_SECTIONS
        confidence = 0.7
        rationale_parts.append("EOS/completed with missing required sections and low budget use")
    elif after_conclusion and eos and pct < 90.0:
        completion = CompletionClass.STOPPED_AFTER_CONCLUSION
        confidence = 0.65
        rationale_parts.append("conclusion language near end with unused budget")
    elif eos and pct < 90.0 and (not sections or section_completion >= 1.0):
        completion = CompletionClass.LIKELY_NATURAL_COMPLETION
        confidence = 0.7
        rationale_parts.append("EOS/completed with substantial unused budget")
    else:
        rationale_parts.append("insufficient signal to classify completion cause")

    # Explicit rules from Phase 2F: do not classify short alone as truncated.
    if (
        actual_output_tokens < requested_max_output_tokens * 0.5
        and not length_stop
        and completion == CompletionClass.LIKELY_BUDGET_EXHAUSTION
    ):
        completion = CompletionClass.UNKNOWN
        confidence = 0.4
        rationale_parts.append(
            "short output cannot be labeled budget exhaustion without length stop"
        )

    return OutputBudgetTelemetry(
        requested_max_output_tokens=requested_max_output_tokens,
        actual_output_tokens=actual_output_tokens,
        finish_reason=finish_reason,
        end_of_sequence_detected=eos,
        percentage_of_token_budget_used=round(pct, 2),
        required_section_completion=round(section_completion, 4),
        final_sentence_complete=final_complete,
        output_stopped_after_conclusion=after_conclusion,
        output_stopped_before_required_sections=before_required,
        completion_class=completion,
        completion_confidence=confidence,
        rationale="; ".join(rationale_parts),
    )
