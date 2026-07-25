"""VehicleDamageAssessment skill helpers (schema-focused)."""

from __future__ import annotations

from typing import Any

from cobra_core.isf.schemas import VehicleDamageAssessmentOutput, validate_skill_output

SKILL_ID = "vehicle_damage_assessment"


def build_vehicle_damage_output(**fields: Any) -> dict[str, Any]:
    """Construct a validated VehicleDamageAssessment structured payload."""
    model = VehicleDamageAssessmentOutput(**fields)
    return validate_skill_output(SKILL_ID, model.model_dump(mode="json"))
