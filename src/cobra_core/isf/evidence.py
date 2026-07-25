"""Evidence type catalog and requirement checks for ISF."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EvidenceType(StrEnum):
    """Declared evidence kinds skills may require."""

    VEHICLE_PHOTOS = "vehicle_photos"
    POLICY_DOCUMENT = "policy_document"
    CONTRACT_DOCUMENT = "contract_document"
    BUDGET_SPREADSHEET = "budget_spreadsheet"
    EVIDENCE_BUNDLE = "evidence_bundle"
    TIMELINE_SOURCE = "timeline_source"
    INTERVIEW_TRANSCRIPT = "interview_transcript"
    DOCUMENT_PAIR = "document_pair"
    OPEN_SOURCE_QUERY = "open_source_query"
    CASE_NOTES = "case_notes"
    GENERIC_FILE = "generic_file"


@dataclass(frozen=True)
class EvidenceRef:
    """
    Reference to evidence supplied by Computer (no file bytes / no prompt text).

    ``evidence_type`` is matched against skill requirements. ``ref_id`` is an
    opaque handle (never logged as content).
    """

    evidence_type: EvidenceType
    ref_id: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (self.ref_id or "").strip():
            raise ValueError("evidence ref_id is required")


def parse_evidence_type(raw: str) -> EvidenceType:
    key = str(raw).strip().lower()
    try:
        return EvidenceType(key)
    except ValueError as exc:
        raise ValueError(f"unknown evidence type: {raw!r}") from exc


def missing_required_evidence(
    required: frozenset[EvidenceType],
    provided: list[EvidenceRef] | tuple[EvidenceRef, ...],
) -> list[EvidenceType]:
    """Return required evidence types not present in the provided set."""
    have = {e.evidence_type for e in provided}
    return sorted(required - have, key=lambda t: t.value)
