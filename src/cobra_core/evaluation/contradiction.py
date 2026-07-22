"""Heuristic contradiction-detection metrics for benchmark responses."""

from __future__ import annotations

import re
from typing import Any

from cobra_core.evaluation.citations import extract_citation_keys
from cobra_core.schemas.benchmark import BenchmarkCase

_CONFLICT_TERMS = re.compile(
    r"\b(contradict|conflict|overlap|inconsistent|disagree|contradiction)\w*\b",
    re.IGNORECASE,
)
_MERGE_WITHOUT_NOTE = re.compile(
    r"\b(both are correct|no conflict|consistent|aligned)\b",
    re.IGNORECASE,
)


def contradiction_metrics(response: str, case: BenchmarkCase) -> dict[str, Any]:
    """
    Conservative contradiction heuristics for reporting.

    Limitations: keyword-based only; does not parse temporal logic or numeric overlap.
    """
    text = response.strip()
    source_keys = [src.citation_key for src in case.supporting_sources]
    cited = extract_citation_keys(text)

    detects_conflict = bool(_CONFLICT_TERMS.search(text))
    cites_multiple_sources = len(set(cited) & set(source_keys)) >= 2 if source_keys else False
    silent_merge = bool(_MERGE_WITHOUT_NOTE.search(text)) and len(source_keys) >= 2

    score = 0.0
    if detects_conflict:
        score += 0.5
    if cites_multiple_sources:
        score += 0.3
    if not silent_merge:
        score += 0.2
    score = min(score, 1.0)

    return {
        "detects_conflict_language": detects_conflict,
        "cites_multiple_sources": cites_multiple_sources,
        "silent_merge_without_conflict_note": silent_merge,
        "cited_source_keys": [key for key in cited if key in source_keys],
        "source_key_count": len(source_keys),
        "heuristic_score": round(score, 4),
        "notes": "Keyword heuristic only; human review required for precision.",
    }
