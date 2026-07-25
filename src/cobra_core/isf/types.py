"""ISF request/result contracts (Computer requests skills, not raw capabilities)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cobra_core.air.capabilities import AirCapability
from cobra_core.isf.confidence import ConfidenceDisposition
from cobra_core.isf.evidence import EvidenceRef, EvidenceType


class SkillExecutionStatus(StrEnum):
    COMPLETED = "completed"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    MISSING_REQUIRED_EVIDENCE = "missing_required_evidence"
    STRUCTURED_OUTPUT_INVALID = "structured_output_invalid"
    FAILED = "failed"


@dataclass(frozen=True)
class SkillRequest:
    """
    Computer-facing skill request.

    Never includes provider/model ids or raw capability lists as the primary
    contract — those are expanded from the skill manifest.
    """

    skill_id: str
    evidence: tuple[EvidenceRef, ...] = ()
    profile_id: str = "default"
    correlation_id: str = ""
    task: str = "investigation"
    skill_version: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityExpansion:
    """Manifest → AIR capability set."""

    skill_id: str
    skill_version: str
    required_capabilities: frozenset[AirCapability]
    optional_capabilities: frozenset[AirCapability]
    effective_capabilities: frozenset[AirCapability]


@dataclass(frozen=True)
class SkillResult:
    """Typed skill outcome (structured payload; not free-form only)."""

    skill_id: str
    skill_version: str
    status: SkillExecutionStatus
    output: dict[str, Any]
    confidence: float
    confidence_disposition: ConfidenceDisposition
    expanded_capabilities: frozenset[AirCapability]
    missing_evidence: tuple[EvidenceType, ...] = ()
    selected_provider: str | None = None
    selected_model: str | None = None
    route_reason: str | None = None
    correlation_id: str = ""
    needs_human_review: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
