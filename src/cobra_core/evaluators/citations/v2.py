"""Citation coverage and precision metrics v2."""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field

from cobra_core.evaluation.citations import extract_citation_keys

EVALUATOR_VERSION = "2.0.0"

_KEY_PATTERN = re.compile(r"\bSRC-[A-Z0-9]+\b|\bS\d+\b")


class CitationValidationIssue(BaseModel):
    model_config = ConfigDict(extra="forbid")

    issue_type: str
    detail: str
    key: str | None = None


class CitationMetricsV2(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evaluator_name: str = "citations"
    evaluator_version: str = EVALUATOR_VERSION
    citation_precision: Annotated[float, Field(ge=0.0, le=1.0)]
    claim_coverage: Annotated[float, Field(ge=0.0, le=1.0)]
    evidence_coverage: Annotated[float, Field(ge=0.0, le=1.0)]
    contrary_evidence_coverage: Annotated[float, Field(ge=0.0, le=1.0)]
    source_diversity: int
    cited_keys: list[str]
    unknown_keys: list[str]
    duplicate_keys_in_list: list[str]
    malformed_keys: list[str]
    issues: list[CitationValidationIssue] = Field(default_factory=list)
    notes: str | None = None


def _normalize_keys(keys: list[str]) -> list[str]:
    return [k.upper() for k in keys]


def validate_citation_keys(
    response: str,
    *,
    allowed_keys: list[str],
) -> list[CitationValidationIssue]:
    issues: list[CitationValidationIssue] = []
    allowed = set(_normalize_keys(allowed_keys))
    found = extract_citation_keys(response)
    # malformed candidates
    for match in re.finditer(r"\bSRC-[^A-Z0-9\s][\w-]*\b", response):
        issues.append(
            CitationValidationIssue(
                issue_type="malformed_key",
                detail=match.group(0),
                key=match.group(0),
            )
        )
    seen: set[str] = set()
    duplicates: set[str] = set()
    for key in found:
        if key in seen:
            duplicates.add(key)
        seen.add(key)
        if key not in allowed:
            issues.append(
                CitationValidationIssue(
                    issue_type="unknown_key",
                    detail="Citation key not in supplied evidence",
                    key=key,
                )
            )
    for key in duplicates:
        issues.append(
            CitationValidationIssue(
                issue_type="duplicate_key",
                detail="Key repeated (informational)",
                key=key,
            )
        )
    return issues


def evaluate_citations_v2(
    response: str,
    *,
    allowed_keys: list[str],
    required_evidence_ids: list[str] | None = None,
    optional_evidence_ids: list[str] | None = None,
    contrary_evidence_ids: list[str] | None = None,
    material_claim_count: int | None = None,
    cited_material_claim_count: int | None = None,
    supporting_source_texts: dict[str, str] | None = None,
) -> CitationMetricsV2:
    """
    Expanded citation metrics.

    Precision = valid cited keys / cited keys.
    Claim coverage = cited material claims / material claims requiring citation.
    Evidence coverage = required evidence IDs cited / required evidence IDs.
    Contrary-evidence coverage = contrary IDs cited / contrary IDs (1.0 if none).
    """
    allowed = _normalize_keys(allowed_keys)
    cited = extract_citation_keys(response)
    allowed_set = set(allowed)
    valid = [k for k in cited if k in allowed_set]
    unknown = [k for k in cited if k not in allowed_set]
    precision = len(valid) / len(cited) if cited else 1.0

    required = _normalize_keys(required_evidence_ids or allowed)
    optional = _normalize_keys(optional_evidence_ids or [])
    contrary = _normalize_keys(contrary_evidence_ids or [])

    evidence_coverage = sum(1 for k in required if k in cited) / len(required) if required else 1.0
    contrary_coverage = sum(1 for k in contrary if k in cited) / len(contrary) if contrary else 1.0

    if material_claim_count is not None and material_claim_count > 0:
        cited_claims = cited_material_claim_count or 0
        claim_coverage = min(1.0, cited_claims / material_claim_count)
    else:
        # Fallback: fraction of response sentences containing a citation when keys exist.
        sentences = [s for s in re.split(r"[.!?]+\s+", response.strip()) if s.strip()]
        if not sentences or not allowed:
            claim_coverage = 1.0
        else:
            with_cite = sum(1 for s in sentences if extract_citation_keys(s))
            claim_coverage = with_cite / len(sentences)

    issues = validate_citation_keys(response, allowed_keys=allowed)
    # citations attached check is advisory via issues only

    dupes = [k for k in cited if cited.count(k) > 1]
    malformed = [i.key for i in issues if i.issue_type == "malformed_key" and i.key]

    return CitationMetricsV2(
        citation_precision=round(precision, 4),
        claim_coverage=round(claim_coverage, 4),
        evidence_coverage=round(evidence_coverage, 4),
        contrary_evidence_coverage=round(contrary_coverage, 4),
        source_diversity=len(set(valid)),
        cited_keys=cited,
        unknown_keys=unknown,
        duplicate_keys_in_list=sorted(set(dupes)),
        malformed_keys=[m for m in malformed if m],
        issues=issues,
        notes=(
            "Do not treat every supplied evidence sentence as mandatory. "
            f"Optional keys ignored for coverage: {optional or 'none'}."
        ),
    )


def metrics_as_dict(result: CitationMetricsV2) -> dict[str, Any]:
    return result.model_dump(mode="json")
