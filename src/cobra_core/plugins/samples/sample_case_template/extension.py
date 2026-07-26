"""Sample case template extension."""

from __future__ import annotations

from typing import Any


def register() -> dict[str, Any]:
    return {
        "extension_id": "sample.case_template.v1",
        "template_id": "auto_collision_intake",
        "title": "Auto Collision Intake (Demo)",
        "fields": ["incident_date", "vin", "claim_number", "photos"],
        "default_skill_ids": ["vehicle_damage_assessment", "policy_compliance_review"],
    }
