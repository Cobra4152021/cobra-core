"""Deterministic evidence ranking (no ML)."""

from __future__ import annotations

import contextlib
from dataclasses import replace
from datetime import datetime

from cobra_core.kef.metadata import type_priority
from cobra_core.kef.types import EvidenceItem, RetrievalQuery


def rank_items(items: list[EvidenceItem], query: RetrievalQuery) -> list[EvidenceItem]:
    """Assign retrieval_score and return sorted descending."""
    scored: list[EvidenceItem] = []
    requested = set(query.ref_ids)
    required = set(query.required_skill_types)
    for item in items:
        score = _score(item, requested=requested, required=required, query=query)
        scored.append(replace(item, retrieval_score=score))
    scored.sort(key=lambda i: (-i.retrieval_score, i.id))
    return scored


def _score(
    item: EvidenceItem,
    *,
    requested: set[str],
    required: set[str],
    query: RetrievalQuery,
) -> float:
    score = 0.0
    # Explicit request match
    if item.id in requested or item.content_reference in requested:
        score += 100.0
    # Required type match
    if item.skill_evidence_type and item.skill_evidence_type in required:
        score += 40.0
    # Metadata match
    for key, expected in (query.metadata_filters or {}).items():
        if item.metadata.get(key) == expected:
            score += 15.0
    # Type priority
    score += type_priority(item.type) / 10.0
    # Connector / item confidence
    score += max(0.0, min(1.0, item.confidence)) * 10.0
    # Manual priority
    manual = item.metadata.get("manual_priority")
    if manual is not None:
        with contextlib.suppress(TypeError, ValueError):
            score += float(manual)
    # Freshness (newer modified_time wins lightly)
    score += _freshness_bonus(item.modified_time or item.created_time)
    return round(score, 4)


def _freshness_bonus(ts: str | None) -> float:
    if not ts:
        return 0.0
    try:
        # Accept ISO-ish timestamps; ignore timezone complexity
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        # Relative to a fixed epoch so ranking stays deterministic across runs
        epoch = datetime(2020, 1, 1, tzinfo=dt.tzinfo)
        days = max(0.0, (dt - epoch).total_seconds() / 86400.0)
        return min(10.0, days / 365.0)
    except ValueError:
        return 0.0
