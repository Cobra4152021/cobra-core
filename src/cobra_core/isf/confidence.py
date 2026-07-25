"""Confidence policy — never invent certainty."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ConfidenceDisposition(StrEnum):
    ACCEPTABLE = "acceptable"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


@dataclass(frozen=True)
class ConfidencePolicy:
    """Per-skill confidence gates."""

    minimum_confidence: float = 0.7
    # When evidence is incomplete, cap confidence at this value.
    incomplete_evidence_cap: float = 0.55
    # Mock / offline structured fills must not claim high certainty.
    mock_confidence_cap: float = 0.5

    def __post_init__(self) -> None:
        for name in ("minimum_confidence", "incomplete_evidence_cap", "mock_confidence_cap"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")

    def disposition(self, score: float) -> ConfidenceDisposition:
        if score + 1e-9 < self.minimum_confidence:
            return ConfidenceDisposition.NEEDS_HUMAN_REVIEW
        return ConfidenceDisposition.ACCEPTABLE

    def clamp(self, score: float, *, incomplete_evidence: bool, mock_path: bool) -> float:
        """Clamp a proposed score; never raise certainty for incomplete/mock paths."""
        s = max(0.0, min(1.0, float(score)))
        if incomplete_evidence:
            s = min(s, self.incomplete_evidence_cap)
        if mock_path:
            s = min(s, self.mock_confidence_cap)
        return round(s, 4)
