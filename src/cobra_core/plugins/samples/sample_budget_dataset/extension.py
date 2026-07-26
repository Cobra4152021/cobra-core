"""Sample budget benchmark dataset extension."""

from __future__ import annotations

from typing import Any


def register() -> dict[str, Any]:
    return {
        "extension_id": "sample.budget_dataset.v1",
        "dataset_id": "sample_budget_plugin_v1",
        "version": "1.0.0",
        "skill_id": "budget_analysis",
        "cases": [
            {
                "case_id": "sample-ba-001",
                "findings": ["duplicate vendor payment"],
                "citations": ["EV-001"],
            }
        ],
    }
