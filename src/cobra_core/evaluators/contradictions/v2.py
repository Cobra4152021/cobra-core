"""Contradiction evaluation submetrics (Phase 2F)."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

EVALUATOR_VERSION = "2.0.0"

_CONFLICT_TERMS = re.compile(
    r"\b(contradict|conflict|inconsist|disagree|mismatch|discrepan|"
    r"however|whereas|but reports?)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_DATE = re.compile(
    r"\b(?:20\d{2}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/20\d{2}|"
    r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+20\d{2})\b",
    re.IGNORECASE,
)
_RECONCILE = re.compile(
    r"\b(must both be true|actually agree|no real conflict|reconcile[sd]? as)\b",
    re.IGNORECASE,
)
_NEXT_EVIDENCE = re.compile(
    r"\b(need|request|obtain|verify|compare|timeline|source of truth|additional evidence)\b",
    re.IGNORECASE,
)


class ContradictionSubmetrics(BaseModel):
    """Separate dimensions — do not collapse into one opaque score."""

    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = "contradictions"
    evaluator_version: str = EVALUATOR_VERSION
    detection: Annotated[float, Field(ge=0.0, le=1.0)]
    localization: Annotated[float, Field(ge=0.0, le=1.0)]
    classification: Annotated[float, Field(ge=0.0, le=1.0)]
    explanation: Annotated[float, Field(ge=0.0, le=1.0)]
    numerical_comparison: Annotated[float, Field(ge=0.0, le=1.0)]
    timeline_comparison: Annotated[float, Field(ge=0.0, le=1.0)]
    preservation_of_competing_accounts: Annotated[float, Field(ge=0.0, le=1.0)]
    avoidance_of_invented_reconciliation: Annotated[float, Field(ge=0.0, le=1.0)]
    resolution_evidence_recommendation: Annotated[float, Field(ge=0.0, le=1.0)]
    confidence_calibration: Annotated[float, Field(ge=0.0, le=1.0)]
    deterministic_notes: list[str] = Field(default_factory=list)
    human_scored_dimensions: list[str] = Field(
        default_factory=lambda: [
            "explanation",
            "classification",
            "confidence_calibration",
        ]
    )
    notes: str = (
        "Deterministic checks approximate detection/localization/numeric/timeline signals. "
        "Explanation quality remains human-scored for official judgments."
    )


def evaluate_contradictions_v2(
    response: str,
    *,
    expected_conflict_markers: list[str] | None = None,
    source_texts: dict[str, str] | None = None,
) -> ContradictionSubmetrics:
    lower = response.lower()
    notes: list[str] = []

    detection = 1.0 if _CONFLICT_TERMS.search(response) else 0.2
    if expected_conflict_markers:
        hits = sum(1 for m in expected_conflict_markers if m.lower() in lower)
        detection = max(detection, hits / len(expected_conflict_markers))

    # Localization: mentions at least two sources or two distinct numbers/dates.
    source_mentions = len(re.findall(r"\bSRC-[A-Z0-9]+\b", response))
    numbers = _NUMBER.findall(response)
    dates = _DATE.findall(response)
    localization = 0.3
    if source_mentions >= 2:
        localization = 0.8
        notes.append("localized_via_multiple_source_keys")
    if len(set(numbers)) >= 2 or len(dates) >= 2:
        localization = max(localization, 0.7)
        notes.append("localized_via_multiple_values")

    classification = 0.5 if detection >= 0.5 else 0.2
    if "metric" in lower or "number" in lower or "count" in lower or "percent" in lower:
        classification = max(classification, 0.6)
    if "time" in lower or "date" in lower or "schedule" in lower:
        classification = max(classification, 0.6)

    # Explanation heuristic: length + comparison language (advisory only).
    explanation = 0.3
    if detection >= 0.5 and len(response.split()) >= 40:
        explanation = 0.55
    if any(term in lower for term in ("because", "while", "whereas", "differs", "reports")):
        explanation = max(explanation, 0.6)
    notes.append("explanation_is_heuristic_not_human_score")

    numerical = 0.2
    if len(set(numbers)) >= 2:
        numerical = 0.75
        notes.append("multiple_numeric_values_compared_or_present")
    elif any(ch.isdigit() for ch in response) and detection >= 0.5:
        numerical = 0.4

    timeline = 0.2
    if len(dates) >= 2 or ("before" in lower and "after" in lower):
        timeline = 0.75
    elif dates:
        timeline = 0.45

    preservation = 0.4
    if source_mentions >= 2 or "both" in lower or "account" in lower:
        preservation = 0.7

    avoidance = 0.85
    if _RECONCILE.search(response):
        avoidance = 0.2
        notes.append("possible_forced_reconciliation_language")

    resolution = 0.3
    if _NEXT_EVIDENCE.search(response):
        resolution = 0.75

    calibration = 0.5
    if any(term in lower for term in ("uncertain", "unclear", "insufficient", "cannot determine")):
        calibration = 0.75
    if any(term in lower for term in ("definitely", "certainly", "proven")):
        calibration = min(calibration, 0.35)

    # Optional: if sources provided, note presence of conflict markers in evidence.
    if source_texts:
        contrary = [
            k
            for k, t in source_texts.items()
            if any(m in t.lower() for m in ("contradict", "conflict", "however", "disagree"))
        ]
        if contrary:
            notes.append(f"source_conflict_markers:{','.join(contrary)}")

    return ContradictionSubmetrics(
        detection=round(detection, 4),
        localization=round(localization, 4),
        classification=round(classification, 4),
        explanation=round(explanation, 4),
        numerical_comparison=round(numerical, 4),
        timeline_comparison=round(timeline, 4),
        preservation_of_competing_accounts=round(preservation, 4),
        avoidance_of_invented_reconciliation=round(avoidance, 4),
        resolution_evidence_recommendation=round(resolution, 4),
        confidence_calibration=round(calibration, 4),
        deterministic_notes=notes,
    )


def submetrics_as_dict(result: ContradictionSubmetrics) -> dict[str, Any]:
    return result.model_dump(mode="json")
