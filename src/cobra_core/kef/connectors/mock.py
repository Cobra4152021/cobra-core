"""Deterministic mock connector with fixture evidence for tests."""

from __future__ import annotations

from typing import Any

from cobra_core.kef.connectors.memory import MemoryConnector
from cobra_core.kef.normalizer import normalize_native
from cobra_core.kef.types import EvidenceKind, HealthStatus


class MockConnector(MemoryConnector):
    connector_id = "mock"

    def __init__(self, *, seed_defaults: bool = True) -> None:
        super().__init__()
        if seed_defaults:
            self.seed_fixtures()

    def health(self) -> HealthStatus:
        return HealthStatus.HEALTHY

    def seed_fixtures(self) -> None:
        fixtures: list[dict[str, Any]] = [
            {
                "id": "mock-policy-001",
                "type": EvidenceKind.POLICY.value,
                "title": "Mock Use-of-Force Policy",
                "skill_evidence_type": "policy_document",
                "integrity_hash": "a" * 32,
                "metadata": {"fixture": True},
            },
            {
                "id": "mock-budget-001",
                "type": EvidenceKind.BUDGET.value,
                "title": "Mock FY Budget",
                "skill_evidence_type": "budget_spreadsheet",
                "integrity_hash": "b" * 32,
                "metadata": {"fixture": True},
            },
            {
                "id": "mock-photo-001",
                "type": EvidenceKind.IMAGE.value,
                "title": "Mock Vehicle Photo",
                "skill_evidence_type": "vehicle_photos",
                "integrity_hash": "c" * 32,
                "metadata": {"fixture": True},
            },
            {
                "id": "mock-contract-001",
                "type": EvidenceKind.CONTRACT.value,
                "title": "Mock Vendor Contract",
                "skill_evidence_type": "contract_document",
                "integrity_hash": "d" * 32,
                "metadata": {"fixture": True},
            },
        ]
        for raw in fixtures:
            self.upsert(normalize_native(raw, connector_id=self.connector_id))
