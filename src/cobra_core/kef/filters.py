"""Deterministic evidence filters (type, metadata, skill requirements)."""

from __future__ import annotations

from cobra_core.kef.metadata import kind_satisfies_skill_type
from cobra_core.kef.types import EvidenceItem, EvidenceKind


def filter_by_kinds(
    items: list[EvidenceItem], kinds: frozenset[EvidenceKind]
) -> list[EvidenceItem]:
    if not kinds:
        return list(items)
    return [i for i in items if i.type in kinds]


def filter_by_skill_types(
    items: list[EvidenceItem], skill_types: frozenset[str]
) -> list[EvidenceItem]:
    if not skill_types:
        return list(items)
    out: list[EvidenceItem] = []
    for item in items:
        if item.skill_evidence_type and item.skill_evidence_type in skill_types:
            out.append(item)
            continue
        if any(kind_satisfies_skill_type(item.type, t) for t in skill_types):
            out.append(item)
    return out


def filter_by_metadata(items: list[EvidenceItem], filters: dict[str, object]) -> list[EvidenceItem]:
    if not filters:
        return list(items)
    out: list[EvidenceItem] = []
    for item in items:
        ok = True
        for key, expected in filters.items():
            actual = item.metadata.get(key)
            if actual != expected:
                ok = False
                break
        if ok:
            out.append(item)
    return out


def missing_skill_types(items: list[EvidenceItem], required: frozenset[str]) -> list[str]:
    """Return required skill evidence types not satisfied by items."""
    have: set[str] = set()
    for item in items:
        if item.skill_evidence_type:
            have.add(item.skill_evidence_type)
        for req in required:
            if kind_satisfies_skill_type(item.type, req):
                have.add(req)
    return sorted(required - have)
