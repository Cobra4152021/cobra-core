"""Collapse duplicate evidence into one logical item."""

from __future__ import annotations

from dataclasses import replace

from cobra_core.kef.types import EvidenceItem


def deduplicate(items: list[EvidenceItem]) -> tuple[list[EvidenceItem], int, dict[str, list[str]]]:
    """
    Collapse duplicates by integrity_hash, then canonical_id.

    Returns (unique_items, removed_count, relationships: survivor -> duplicates).
    """
    if not items:
        return [], 0, {}

    by_key: dict[str, EvidenceItem] = {}
    relationships: dict[str, list[str]] = {}
    removed = 0

    for item in items:
        key = _dedupe_key(item)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = item
            continue
        removed += 1
        survivor, loser = _prefer(existing, item)
        by_key[key] = survivor
        relationships.setdefault(survivor.id, []).append(loser.id)
        # Mark loser relationship on a copy kept only in relationships; survivor stays clean.

    unique = list(by_key.values())
    # Annotate survivors that absorbed duplicates
    annotated: list[EvidenceItem] = []
    for item in unique:
        dups = relationships.get(item.id) or []
        if dups:
            meta = dict(item.metadata)
            meta["duplicate_ids"] = dups
            annotated.append(replace(item, metadata=meta))
        else:
            annotated.append(item)
    return annotated, removed, relationships


def _dedupe_key(item: EvidenceItem) -> str:
    if item.integrity_hash:
        return f"hash:{item.integrity_hash}"
    if item.canonical_id:
        return f"canon:{item.canonical_id}"
    return f"id:{item.id}"


def _prefer(a: EvidenceItem, b: EvidenceItem) -> tuple[EvidenceItem, EvidenceItem]:
    """Prefer higher confidence, then higher retrieval_score, then stable id order."""
    if b.confidence > a.confidence:
        return b, a
    if b.confidence < a.confidence:
        return a, b
    if b.retrieval_score > a.retrieval_score:
        return b, a
    if b.retrieval_score < a.retrieval_score:
        return a, b
    if b.id < a.id:
        return b, a
    return a, b
