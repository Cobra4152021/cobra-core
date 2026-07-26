"""Validate public EV citation aliases against the retrieved evidence set."""

from __future__ import annotations

import re
from typing import Any

from cobra_core.kef.errors import KefError, KefErrorCode
from cobra_core.kef.types import Citation

_EV = re.compile(r"\bEV-\d{3,}\b")


def validate_citations(
    output: dict[str, Any],
    citations: list[Citation],
    denied_ids: set[str],
    integrity_failed_ids: set[str],
) -> list[str]:
    known = {citation.public_id(): citation.evidence_id for citation in citations}
    text = str(output)
    violations: list[str] = []
    for label in _EV.findall(text):
        evidence_id = known.get(label)
        if evidence_id is None:
            violations.append(f"unknown:{label}")
        elif evidence_id in denied_ids:
            violations.append(f"denied:{label}")
        elif evidence_id in integrity_failed_ids:
            violations.append(f"integrity_failed:{label}")
    return violations


def require_valid_citations(
    output: dict[str, Any],
    citations: list[Citation],
    denied_ids: set[str],
    integrity_failed_ids: set[str],
) -> None:
    if validate_citations(output, citations, denied_ids, integrity_failed_ids):
        raise KefError(KefErrorCode.INVALID_EVIDENCE_CITATION, "invalid evidence citation")
