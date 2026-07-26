"""Citation engine — attach evidence references to skill findings."""

from __future__ import annotations

from typing import Any

from cobra_core.kef.types import Citation, EvidenceItem


def assign_citation_labels(items: list[EvidenceItem]) -> list[Citation]:
    """Produce EV-001 style citations in ranked order."""
    citations: list[Citation] = []
    for idx, item in enumerate(items, start=1):
        label = f"EV-{idx:03d}"
        citations.append(
            Citation(
                evidence_id=item.id,
                label=label,
                skill_evidence_type=item.skill_evidence_type,
            )
        )
    return citations


def citation_ids(citations: list[Citation]) -> list[str]:
    return [c.public_id() for c in citations]


def attach_citations_to_output(
    output: dict[str, Any],
    citations: list[Citation],
    *,
    findings_key: str | None = None,
) -> dict[str, Any]:
    """
    Ensure skill output includes supporting evidence references.

    Adds top-level ``citations`` list. When findings exist, each finding dict
    may receive citations if structured that way; string findings stay unchanged
    and share the top-level citation set (no unsupported empty set when evidence
    was retrieved).
    """
    out = dict(output)
    ids = citation_ids(citations)
    out["citations"] = ids
    # Structured finding objects (list of dicts)
    key = findings_key or _detect_findings_key(out)
    if key and isinstance(out.get(key), list):
        new_findings: list[Any] = []
        for entry in out[key]:
            if isinstance(entry, dict):
                enriched = dict(entry)
                if "citations" not in enriched:
                    enriched["citations"] = ids
                new_findings.append(enriched)
            else:
                new_findings.append(entry)
        out[key] = new_findings
    return out


def _detect_findings_key(output: dict[str, Any]) -> str | None:
    for key in ("findings", "damage_locations", "key_statements", "events", "patterns"):
        if key in output:
            return key
    return None


def require_citations_for_conclusions(
    output: dict[str, Any], citations: list[Citation]
) -> list[str]:
    """
    Return violation messages when conclusions lack citations.

    Conservative: if citations list is non-empty, top-level is satisfied.
    If output claims findings but citations empty → violation.
    """
    violations: list[str] = []
    ids = citation_ids(citations)
    has_conclusion = bool(
        output.get("findings")
        or output.get("summary")
        or output.get("damage_locations")
        or output.get("compliance_status") not in (None, "", "unknown")
    )
    if has_conclusion and not ids:
        violations.append("conclusions_without_citations")
    return violations
