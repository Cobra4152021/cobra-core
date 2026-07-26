"""Evidence metadata helpers and ISF ↔ KEF type mapping."""

from __future__ import annotations

from cobra_core.isf.evidence import EvidenceType
from cobra_core.kef.types import EvidenceKind

# Skill evidence type → primary KEF kind
_SKILL_TO_KIND: dict[str, EvidenceKind] = {
    EvidenceType.VEHICLE_PHOTOS.value: EvidenceKind.IMAGE,
    EvidenceType.POLICY_DOCUMENT.value: EvidenceKind.POLICY,
    EvidenceType.CONTRACT_DOCUMENT.value: EvidenceKind.CONTRACT,
    EvidenceType.BUDGET_SPREADSHEET.value: EvidenceKind.BUDGET,
    EvidenceType.EVIDENCE_BUNDLE.value: EvidenceKind.DOCUMENT,
    EvidenceType.TIMELINE_SOURCE.value: EvidenceKind.TIMELINE,
    EvidenceType.INTERVIEW_TRANSCRIPT.value: EvidenceKind.AUDIO_TRANSCRIPT,
    EvidenceType.DOCUMENT_PAIR.value: EvidenceKind.DOCUMENT,
    EvidenceType.OPEN_SOURCE_QUERY.value: EvidenceKind.REPORT,
    EvidenceType.CASE_NOTES.value: EvidenceKind.CASE_NOTE,
    EvidenceType.GENERIC_FILE.value: EvidenceKind.DOCUMENT,
}

# KEF kind → acceptable skill evidence types (for reverse matching)
_KIND_TO_SKILL: dict[EvidenceKind, frozenset[str]] = {
    EvidenceKind.IMAGE: frozenset(
        {EvidenceType.VEHICLE_PHOTOS.value, EvidenceType.GENERIC_FILE.value}
    ),
    EvidenceKind.POLICY: frozenset({EvidenceType.POLICY_DOCUMENT.value}),
    EvidenceKind.CONTRACT: frozenset({EvidenceType.CONTRACT_DOCUMENT.value}),
    EvidenceKind.BUDGET: frozenset({EvidenceType.BUDGET_SPREADSHEET.value}),
    EvidenceKind.SPREADSHEET: frozenset({EvidenceType.BUDGET_SPREADSHEET.value}),
    EvidenceKind.DOCUMENT: frozenset(
        {
            EvidenceType.EVIDENCE_BUNDLE.value,
            EvidenceType.DOCUMENT_PAIR.value,
            EvidenceType.GENERIC_FILE.value,
            EvidenceType.POLICY_DOCUMENT.value,
            EvidenceType.CONTRACT_DOCUMENT.value,
        }
    ),
    EvidenceKind.PDF: frozenset(
        {
            EvidenceType.POLICY_DOCUMENT.value,
            EvidenceType.CONTRACT_DOCUMENT.value,
            EvidenceType.GENERIC_FILE.value,
            EvidenceType.DOCUMENT_PAIR.value,
        }
    ),
    EvidenceKind.DOCX: frozenset(
        {
            EvidenceType.POLICY_DOCUMENT.value,
            EvidenceType.CONTRACT_DOCUMENT.value,
            EvidenceType.GENERIC_FILE.value,
        }
    ),
    EvidenceKind.TIMELINE: frozenset({EvidenceType.TIMELINE_SOURCE.value}),
    EvidenceKind.AUDIO_TRANSCRIPT: frozenset({EvidenceType.INTERVIEW_TRANSCRIPT.value}),
    EvidenceKind.VIDEO_TRANSCRIPT: frozenset({EvidenceType.INTERVIEW_TRANSCRIPT.value}),
    EvidenceKind.CASE_NOTE: frozenset({EvidenceType.CASE_NOTES.value}),
    EvidenceKind.REPORT: frozenset(
        {EvidenceType.OPEN_SOURCE_QUERY.value, EvidenceType.EVIDENCE_BUNDLE.value}
    ),
    EvidenceKind.EMAIL: frozenset({EvidenceType.GENERIC_FILE.value, EvidenceType.CASE_NOTES.value}),
}


def skill_type_to_kind(skill_type: str) -> EvidenceKind:
    key = (skill_type or "").strip().lower()
    return _SKILL_TO_KIND.get(key, EvidenceKind.DOCUMENT)


def kind_satisfies_skill_type(kind: EvidenceKind, skill_type: str) -> bool:
    key = (skill_type or "").strip().lower()
    accepted = _KIND_TO_SKILL.get(kind)
    if accepted and key in accepted:
        return True
    return skill_type_to_kind(key) == kind


def type_priority(kind: EvidenceKind) -> int:
    """Higher = preferred in ranking ties."""
    order = {
        EvidenceKind.POLICY: 100,
        EvidenceKind.CONTRACT: 95,
        EvidenceKind.BUDGET: 90,
        EvidenceKind.IMAGE: 85,
        EvidenceKind.TIMELINE: 80,
        EvidenceKind.CASE_NOTE: 75,
        EvidenceKind.AUDIO_TRANSCRIPT: 70,
        EvidenceKind.VIDEO_TRANSCRIPT: 70,
        EvidenceKind.PDF: 65,
        EvidenceKind.DOCX: 60,
        EvidenceKind.SPREADSHEET: 60,
        EvidenceKind.REPORT: 55,
        EvidenceKind.DOCUMENT: 50,
        EvidenceKind.EMAIL: 45,
    }
    return order.get(kind, 10)
