"""Semantic versus exact-format scoring (Phase 2F)."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from cobra_core.evaluators.format_compliance.parser import (
    ParserMode,
    StructuredParseResult,
    parse_finding_risk_next,
)

EVALUATOR_VERSION = "2.0.0"


class FormatComplianceResult(BaseModel):
    """Separated scores — do not auto-collapse into one overall score."""

    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = "format_compliance"
    evaluator_version: str = EVALUATOR_VERSION
    semantic_score: Annotated[float, Field(ge=0.0, le=1.0)]
    exact_format_score: Annotated[float, Field(ge=0.0, le=1.0)]
    parse_success: bool
    tolerant_parse_success: bool
    missing_fields: list[str] = Field(default_factory=list)
    extra_fields: list[str] = Field(default_factory=list)
    label_variations: list[str] = Field(default_factory=list)
    ordering_errors: list[str] = Field(default_factory=list)
    delimiter_errors: list[str] = Field(default_factory=list)
    semantic_errors: list[str] = Field(default_factory=list)
    strict_parse: StructuredParseResult
    tolerant_parse: StructuredParseResult
    policy_note: str


def evaluate_format_compliance_v2(
    response: str,
    *,
    required_fields: list[str] | None = None,
    required_meanings: dict[str, list[str]] | None = None,
) -> FormatComplianceResult:
    """
    Score semantic field presence separately from exact syntax.

    ``required_meanings`` maps field -> keywords that indicate semantic content.
    """
    required = required_fields or ["FINDING", "RISK", "NEXT"]
    meanings = required_meanings or {
        "FINDING": ["outdated", "dependency", "scanner", "found", "issue"],
        "RISK": ["risk", "vulnerab", "security", "exposure", "outdated"],
        "NEXT": ["update", "patch", "upgrade", "remediat", "review", "next"],
    }

    strict = parse_finding_risk_next(response, mode=ParserMode.STRICT, required_fields=required)
    tolerant = parse_finding_risk_next(response, mode=ParserMode.TOLERANT, required_fields=required)

    label_variations: list[str] = []
    if tolerant.success and not strict.success:
        label_variations.append("markdown_or_case_variant_labels")
    delimiter_errors: list[str] = []
    if ":" not in response and any(k in response.upper() for k in required):
        delimiter_errors.append("missing_colon_delimiters")

    # Semantic: required meanings present even if syntax fails.
    semantic_hits = 0
    semantic_errors: list[str] = []
    lower = response.lower()
    for field in required:
        keys = meanings.get(field, [])
        if any(k in lower for k in keys):
            semantic_hits += 1
        else:
            # Also accept tolerant-parsed values as semantic carriers.
            value = tolerant.fields.get(field, "").lower()
            if value and len(value) >= 3:
                semantic_hits += 1
            else:
                semantic_errors.append(f"missing_semantic:{field}")

    semantic_score = semantic_hits / len(required) if required else 1.0
    exact_format_score = 1.0 if strict.success else (0.4 if tolerant.success else 0.0)

    return FormatComplianceResult(
        semantic_score=round(semantic_score, 4),
        exact_format_score=round(exact_format_score, 4),
        parse_success=strict.success,
        tolerant_parse_success=tolerant.success,
        missing_fields=strict.missing_fields if not tolerant.success else tolerant.missing_fields,
        extra_fields=tolerant.extra_fields,
        label_variations=label_variations,
        ordering_errors=[],
        delimiter_errors=delimiter_errors,
        semantic_errors=semantic_errors,
        strict_parse=strict,
        tolerant_parse=tolerant,
        policy_note=(
            "For strict machine interoperability, exact_format_score may be mandatory. "
            "For human-facing investigation reports, harmless markdown/punctuation "
            "variation must not be scored as a semantic failure."
        ),
    )
