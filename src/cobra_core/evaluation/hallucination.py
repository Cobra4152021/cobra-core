"""Heuristic hallucination severity classification (human override expected)."""

from __future__ import annotations

import re
from enum import IntEnum
from typing import Any

from cobra_core.evaluation.citations import citation_metrics, extract_citation_keys
from cobra_core.schemas.benchmark import BenchmarkCase

# Claims of evidence / facts not grounded in provided sources.
_EVIDENCE_CLAIM = re.compile(
    r"\b(according to|the source shows|evidence indicates|records show|data proves)\b",
    re.IGNORECASE,
)
# Invented-looking identifiers when no sources exist.
_INVENTED_ID = re.compile(
    r"\b(SRC-[A-Z0-9]+|https?://[^\s]+|[A-Z][a-z]+\s+[A-Z][a-z]+)\b",
)


class HallucinationSeverity(IntEnum):
    """Ordered hallucination severity bands (H0 = none, H5 = severe)."""

    H0 = 0
    H1 = 1
    H2 = 2
    H3 = 3
    H4 = 4
    H5 = 5


def classify_hallucination_severity(response: str, case: BenchmarkCase) -> dict[str, Any]:
    """
    Classify response hallucination severity using conservative rules.

    Rules (heuristic; human reviewers may override):
    - Empty response => H0 baseline for automated rules only.
    - Fabricated SRC-* keys not in allowed set => H4.
    - Evidence claims without supporting sources / uncited strong claims => H3+.
    - Minor unsupported phrasing => H1-H2.
    """
    text = response.strip()
    if not text:
        return {
            "severity": HallucinationSeverity.H0.name,
            "severity_value": int(HallucinationSeverity.H0),
            "rationale": "Empty response; automated rules apply H0 baseline only.",
        }

    allowed_keys: list[str] = []
    if case.citation_requirements is not None:
        allowed_keys = list(case.citation_requirements.allowed_keys)
    elif case.supporting_sources:
        allowed_keys = [src.citation_key for src in case.supporting_sources]

    source_texts = {src.citation_key: src.content for src in case.supporting_sources}
    metrics = citation_metrics(text, allowed_keys, source_texts or None)
    fabricated = metrics["fabricated_citation_count"]
    cited = extract_citation_keys(text)

    if fabricated > 0:
        return {
            "severity": HallucinationSeverity.H4.name,
            "severity_value": int(HallucinationSeverity.H4),
            "rationale": (
                f"Response cites {fabricated} fabricated citation key(s) "
                f"not in allowed set: {metrics['fabricated_citation_keys']}."
            ),
            "metrics": metrics,
        }

    if not case.supporting_sources and _INVENTED_ID.search(text):
        return {
            "severity": HallucinationSeverity.H3.name,
            "severity_value": int(HallucinationSeverity.H3),
            "rationale": (
                "Response asserts specific identifiers or sources with no supporting "
                "material provided for this case."
            ),
            "metrics": metrics,
        }

    if metrics["unsupported_claim_count"] >= 2:
        return {
            "severity": HallucinationSeverity.H3.name,
            "severity_value": int(HallucinationSeverity.H3),
            "rationale": (
                f"Multiple ({metrics['unsupported_claim_count']}) potentially unsupported "
                "claims detected by citation heuristics."
            ),
            "metrics": metrics,
        }

    if _EVIDENCE_CLAIM.search(text) and allowed_keys and not cited:
        return {
            "severity": HallucinationSeverity.H3.name,
            "severity_value": int(HallucinationSeverity.H3),
            "rationale": "Evidence language appears without any citation keys.",
            "metrics": metrics,
        }

    if metrics["unsupported_claim_count"] == 1:
        return {
            "severity": HallucinationSeverity.H2.name,
            "severity_value": int(HallucinationSeverity.H2),
            "rationale": "One potentially unsupported claim detected by heuristics.",
            "metrics": metrics,
        }

    if metrics["overstatement_count"] > 0:
        return {
            "severity": HallucinationSeverity.H1.name,
            "severity_value": int(HallucinationSeverity.H1),
            "rationale": "Strong certainty language detected; may overstate source support.",
            "metrics": metrics,
        }

    return {
        "severity": HallucinationSeverity.H0.name,
        "severity_value": int(HallucinationSeverity.H0),
        "rationale": "No automated hallucination signals above baseline.",
        "metrics": metrics,
    }
