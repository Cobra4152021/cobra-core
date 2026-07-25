"""
Investigation Skills Framework (ISF) — KC-024.

Computer requests an investigation skill. ISF expands capabilities and
evidence requirements; AIR selects the provider/model.
"""

from __future__ import annotations

from cobra_core.isf.audit import ISF_AUDIT, IsfAuditLog
from cobra_core.isf.computer_adapter import ComputerIsfAdapter
from cobra_core.isf.confidence import ConfidenceDisposition, ConfidencePolicy
from cobra_core.isf.enabled import isf_enabled
from cobra_core.isf.engine import SkillEngine, expand_skill_capabilities
from cobra_core.isf.errors import IsfError, IsfErrorCode
from cobra_core.isf.evidence import EvidenceRef, EvidenceType
from cobra_core.isf.manifest import SkillManifest
from cobra_core.isf.metrics import ISF_METRICS, IsfMetrics
from cobra_core.isf.registry import SKILL_REGISTRY, SkillRegistry
from cobra_core.isf.schemas import (
    SCHEMA_BY_SKILL_ID,
    VehicleDamageAssessmentOutput,
    validate_skill_output,
)
from cobra_core.isf.skills import builtin_skill_manifests, register_builtin_skills
from cobra_core.isf.types import (
    CapabilityExpansion,
    SkillExecutionStatus,
    SkillRequest,
    SkillResult,
)

# Ensure builtins are registered on import.
register_builtin_skills()

__all__ = [
    "ISF_AUDIT",
    "ISF_METRICS",
    "SCHEMA_BY_SKILL_ID",
    "SKILL_REGISTRY",
    "CapabilityExpansion",
    "ComputerIsfAdapter",
    "ConfidenceDisposition",
    "ConfidencePolicy",
    "EvidenceRef",
    "EvidenceType",
    "IsfAuditLog",
    "IsfError",
    "IsfErrorCode",
    "IsfMetrics",
    "SkillEngine",
    "SkillExecutionStatus",
    "SkillManifest",
    "SkillRegistry",
    "SkillRequest",
    "SkillResult",
    "VehicleDamageAssessmentOutput",
    "builtin_skill_manifests",
    "expand_skill_capabilities",
    "isf_enabled",
    "register_builtin_skills",
    "validate_skill_output",
]
