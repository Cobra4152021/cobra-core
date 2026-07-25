"""Built-in investigation skill manifests (self-registering)."""

from __future__ import annotations

from cobra_core.air.capabilities import AirCapability
from cobra_core.isf.confidence import ConfidencePolicy
from cobra_core.isf.evidence import EvidenceType
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.registry import SKILL_REGISTRY, SkillRegistry

_CAPS = AirCapability
_EV = EvidenceType


def builtin_skill_manifests() -> list[SkillManifest]:
    """Return built-in skill manifests (does not register)."""
    return [
        SkillManifest(
            id="vehicle_damage_assessment",
            title="VehicleDamageAssessment",
            version="1.0.0",
            description="Assess vehicle damage from photos with structured findings.",
            required_capabilities=frozenset(
                {_CAPS.VISION, _CAPS.REASONING, _CAPS.STRUCTURED_OUTPUT}
            ),
            optional_capabilities=frozenset({_CAPS.OCR}),
            required_evidence_types=frozenset({_EV.VEHICLE_PHOTOS}),
            confidence_policy=ConfidencePolicy(minimum_confidence=0.75),
        ),
        SkillManifest(
            id="policy_compliance_review",
            title="PolicyComplianceReview",
            version="1.0.0",
            description="Review policy documents for compliance findings.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.SUMMARIZATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            optional_capabilities=frozenset({_CAPS.OCR, _CAPS.LONG_CONTEXT}),
            required_evidence_types=frozenset({_EV.POLICY_DOCUMENT}),
            confidence_policy=ConfidencePolicy(minimum_confidence=0.7),
        ),
        SkillManifest(
            id="contract_analysis",
            title="ContractAnalysis",
            version="1.0.0",
            description="Analyze contracts for parties, obligations, and risks.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.SUMMARIZATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            optional_capabilities=frozenset({_CAPS.LONG_CONTEXT, _CAPS.OCR}),
            required_evidence_types=frozenset({_EV.CONTRACT_DOCUMENT}),
        ),
        SkillManifest(
            id="budget_analysis",
            title="BudgetAnalysis",
            version="1.0.0",
            description="Analyze budgets for variances and anomalies.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.CLASSIFICATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            required_evidence_types=frozenset({_EV.BUDGET_SPREADSHEET}),
            confidence_policy=ConfidencePolicy(minimum_confidence=0.7),
        ),
        SkillManifest(
            id="evidence_summary",
            title="EvidenceSummary",
            version="1.0.0",
            description="Summarize an evidence bundle with themes and gaps.",
            required_capabilities=frozenset(
                {_CAPS.SUMMARIZATION, _CAPS.REASONING, _CAPS.STRUCTURED_OUTPUT}
            ),
            required_evidence_types=frozenset({_EV.EVIDENCE_BUNDLE}),
            supported_profiles=frozenset({"default", "research", "analysis", "offline", "coding"}),
        ),
        SkillManifest(
            id="timeline_construction",
            title="TimelineConstruction",
            version="1.0.0",
            description="Construct an investigative timeline from sources.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.SUMMARIZATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            required_evidence_types=frozenset({_EV.TIMELINE_SOURCE}),
        ),
        SkillManifest(
            id="pattern_detection",
            title="PatternDetection",
            version="1.0.0",
            description="Detect patterns across case notes and evidence.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.CLASSIFICATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            optional_capabilities=frozenset({_CAPS.LONG_CONTEXT}),
            required_evidence_types=frozenset({_EV.CASE_NOTES}),
        ),
        SkillManifest(
            id="open_source_research",
            title="OpenSourceResearch",
            version="1.0.0",
            description="Structure open-source research findings and open questions.",
            required_capabilities=frozenset(
                {_CAPS.RESEARCH, _CAPS.REASONING, _CAPS.STRUCTURED_OUTPUT}
            ),
            required_evidence_types=frozenset({_EV.OPEN_SOURCE_QUERY}),
            supported_profiles=frozenset({"default", "research", "analysis"}),
        ),
        SkillManifest(
            id="interview_summary",
            title="InterviewSummary",
            version="1.0.0",
            description="Summarize interview transcripts with key statements.",
            required_capabilities=frozenset(
                {_CAPS.SUMMARIZATION, _CAPS.REASONING, _CAPS.STRUCTURED_OUTPUT}
            ),
            required_evidence_types=frozenset({_EV.INTERVIEW_TRANSCRIPT}),
        ),
        SkillManifest(
            id="document_comparison",
            title="DocumentComparison",
            version="1.0.0",
            description="Compare documents for agreements and material conflicts.",
            required_capabilities=frozenset(
                {_CAPS.REASONING, _CAPS.SUMMARIZATION, _CAPS.STRUCTURED_OUTPUT}
            ),
            optional_capabilities=frozenset({_CAPS.LONG_CONTEXT}),
            required_evidence_types=frozenset({_EV.DOCUMENT_PAIR}),
        ),
    ]


def register_builtin_skills(registry: SkillRegistry | None = None) -> SkillRegistry:
    """Register all built-in skills on the given registry (default: process-wide)."""
    reg = registry if registry is not None else SKILL_REGISTRY
    for manifest in builtin_skill_manifests():
        reg.register(manifest)
    return reg


# Self-register on import.
register_builtin_skills()
