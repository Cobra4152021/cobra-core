"""Skill manifest — registration contract (provider-/model-neutral)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from cobra_core.air.capabilities import AirCapability
from cobra_core.isf.confidence import ConfidencePolicy
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import EvidenceType
from cobra_core.isf.schemas import SCHEMA_BY_SKILL_ID


@dataclass(frozen=True)
class SkillManifest:
    """
    Declares what an investigation skill requires and produces.

    Computer selects by ``id`` only — never by provider or model.
    """

    id: str
    title: str
    version: str
    description: str
    required_capabilities: frozenset[AirCapability]
    optional_capabilities: frozenset[AirCapability] = field(default_factory=frozenset)
    required_evidence_types: frozenset[EvidenceType] = field(default_factory=frozenset)
    supported_profiles: frozenset[str] = field(
        default_factory=lambda: frozenset({"default", "research", "analysis", "offline"})
    )
    confidence_policy: ConfidencePolicy = field(default_factory=ConfidencePolicy)
    output_schema_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not (self.id or "").strip():
            raise IsfError(IsfErrorCode.MANIFEST_INVALID, "skill id is required")
        if not (self.version or "").strip():
            raise IsfError(IsfErrorCode.MANIFEST_INVALID, "skill version is required")
        if not self.required_capabilities:
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                "skill must declare required capabilities",
            )
        schema_key = self.output_schema_id or self.id
        if schema_key not in SCHEMA_BY_SKILL_ID:
            raise IsfError(
                IsfErrorCode.MANIFEST_INVALID,
                f"output schema not registered for skill: {schema_key}",
            )

    @property
    def schema_key(self) -> str:
        return self.output_schema_id or self.id

    def effective_capabilities(self) -> frozenset[AirCapability]:
        """Capabilities sent to AIR (required ∪ optional for matching richness)."""
        # AIR matching is subset-based: request required only so providers aren't
        # over-constrained by optional caps.
        return frozenset(self.required_capabilities)
