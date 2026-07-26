"""Sample vehicle skill extension payload (demonstration only)."""

from __future__ import annotations

from typing import Any


def register() -> dict[str, Any]:
    return {
        "extension_id": "sample.vehicle_skill.v1",
        "skill_id": "sample_vehicle_damage_demo",
        "title": "Sample Vehicle Damage (Demo)",
        "version": "1.0.0",
        "description": "Reference plugin skill declaration; not wired into SKILL_REGISTRY.",
        "required_evidence_types": ["vehicle_photos"],
        "output_schema_hint": "vehicle_damage_assessment",
    }
