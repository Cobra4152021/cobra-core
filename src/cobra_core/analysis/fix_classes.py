"""Fix-class taxonomy for Phase 2E improvement proposals (Part 16)."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from cobra_core.analysis.weakness import WeaknessClass


class FixClass(StrEnum):
    """Improvement class — training only after Class 1–3 exhaustion."""

    RUNTIME_CONFIGURATION = "class_1_runtime"
    PROMPT_INTERFACE = "class_2_prompt"
    EVALUATION_FRAMEWORK = "class_3_evaluation"
    MODEL_ADAPTATION_CANDIDATE = "class_4_adaptation"


class FixProposal(BaseModel):
    """Proposed improvement tied to weakness evidence."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    weakness_id: Annotated[str, Field(min_length=1)]
    description: Annotated[str, Field(min_length=1)]
    fix_class: FixClass
    related_weakness_classes: list[WeaknessClass] = Field(default_factory=list)
    reproducible: bool = False
    persists_after_prompt_runtime_controls: bool | None = None
    primarily_benchmark_defect: bool = False
    material_investigation_risk: bool = False
    notes: str | None = None


def validate_class4_eligibility(proposal: FixProposal) -> list[str]:
    """
    Return errors if a Class 4 proposal lacks required evidence.

    Class 4 requires: reproducible, persists after controls, not primarily
    benchmark defect, and material investigation risk.
    """
    errors: list[str] = []
    if proposal.fix_class != FixClass.MODEL_ADAPTATION_CANDIDATE:
        return errors
    if not proposal.reproducible:
        errors.append("Class 4 requires reproducible=true")
    if proposal.persists_after_prompt_runtime_controls is not True:
        errors.append(
            "Class 4 requires persists_after_prompt_runtime_controls=true "
            "(diagnostics must confirm persistence)"
        )
    if proposal.primarily_benchmark_defect:
        errors.append("Class 4 forbidden when primarily_benchmark_defect=true")
    if not proposal.material_investigation_risk:
        errors.append("Class 4 requires material_investigation_risk=true")
    return errors
