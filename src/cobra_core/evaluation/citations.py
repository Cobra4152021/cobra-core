"""Citation extraction and heuristic citation-quality metrics."""

from __future__ import annotations

import re
from typing import Any

# Stable citation keys like SRC-A, SRC-P1, SRC-B12.
_CITATION_KEY_PATTERN = re.compile(r"\bSRC-[A-Z0-9]+\b")

# Sentences split on punctuation (conservative heuristic).
_SENTENCE_SPLIT = re.compile(r"[.!?]+\s+")

# Strong certainty language used for overstatement heuristics.
_OVERSTATEMENT_TERMS = re.compile(
    r"\b(definitely|certainly|proven|confirmed|undeniably|without doubt)\b",
    re.IGNORECASE,
)


def extract_citation_keys(text: str) -> list[str]:
    """Return unique citation keys (e.g. SRC-A) in first-seen order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for match in _CITATION_KEY_PATTERN.finditer(text):
        key = match.group(0)
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


def _normalize_for_substring(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def _claim_sentences(text: str) -> list[str]:
    stripped = text.strip()
    if not stripped:
        return []
    parts = [part.strip() for part in _SENTENCE_SPLIT.split(stripped) if part.strip()]
    return parts if parts else [stripped]


def citation_metrics(
    response: str,
    allowed_keys: list[str],
    supporting_source_texts: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Compute conservative citation-quality metrics.

    Heuristics (documented limitations):
    - ``citation_precision``: fraction of cited keys that are allowed.
    - ``citation_coverage``: fraction of allowed keys that appear at least once.
    - ``fabricated_citation_count``: cited keys not in ``allowed_keys``.
    - ``unsupported_claim_count``: sentences without any citation key when citations
      are expected; if ``supporting_source_texts`` is provided, also counts sentences
      whose content is not loosely supported by any cited source text.
    - ``overstatement_count``: sentences with strong certainty terms not near a citation
      key (0 when ``supporting_source_texts`` is None — unknown evidence strength).
    - ``omitted_contrary_evidence_count``: 0 by default; only incremented when source
      texts contain obvious conflict markers and the response cites none of them.
    """
    cited = extract_citation_keys(response)
    allowed_set = set(allowed_keys)
    fabricated = [key for key in cited if key not in allowed_set]
    valid_cited = [key for key in cited if key in allowed_set]

    precision = len(valid_cited) / len(cited) if cited else 1.0
    coverage = (
        sum(1 for key in allowed_keys if key in cited) / len(allowed_keys) if allowed_keys else 1.0
    )

    unsupported_claim_count = 0
    if allowed_keys:
        for sentence in _claim_sentences(response):
            if extract_citation_keys(sentence):
                if supporting_source_texts:
                    keys_in_sentence = extract_citation_keys(sentence)
                    supported = False
                    for key in keys_in_sentence:
                        source_text = supporting_source_texts.get(key, "")
                        if not source_text:
                            continue
                        # Loose overlap: any 3+ word chunk from source appears in sentence.
                        tokens = [t for t in re.findall(r"[a-z0-9]{4,}", source_text.lower())]
                        sentence_norm = _normalize_for_substring(sentence)
                        if any(token in sentence_norm for token in tokens[:12]):
                            supported = True
                            break
                    if not supported and keys_in_sentence:
                        unsupported_claim_count += 1
            else:
                unsupported_claim_count += 1

    overstatement_count = 0
    if supporting_source_texts is not None:
        for sentence in _claim_sentences(response):
            if _OVERSTATEMENT_TERMS.search(sentence) and not extract_citation_keys(sentence):
                overstatement_count += 1

    omitted_contrary_evidence_count = 0
    if supporting_source_texts:
        conflict_markers = ("contradict", "conflict", "however", "disagree", "overlap")
        contrary_keys = [
            key
            for key, text in supporting_source_texts.items()
            if any(marker in text.lower() for marker in conflict_markers)
        ]
        if contrary_keys and not any(key in cited for key in contrary_keys):
            omitted_contrary_evidence_count = len(contrary_keys)

    return {
        "citation_precision": round(precision, 4),
        "citation_coverage": round(coverage, 4),
        "fabricated_citation_count": len(fabricated),
        "fabricated_citation_keys": fabricated,
        "unsupported_claim_count": unsupported_claim_count,
        "overstatement_count": overstatement_count,
        "omitted_contrary_evidence_count": omitted_contrary_evidence_count,
        "cited_keys": cited,
        "allowed_keys": list(allowed_keys),
    }
