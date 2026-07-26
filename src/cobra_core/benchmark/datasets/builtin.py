"""Versioned built-in gold datasets for Investigation Skills (KC-030)."""

from __future__ import annotations

from typing import Any

from cobra_core.benchmark.registry import DATASET_REGISTRY, DatasetRegistry
from cobra_core.benchmark.schemas import (
    BenchmarkCase,
    BenchmarkDataset,
    ExpectedEvidence,
    GoldStandard,
)

_VERSION = "1.0.0"


def _case(
    case_id: str,
    skill_id: str,
    dataset_id: str,
    *,
    task: str,
    evidence: list[tuple[str, str]],
    findings: list[str],
    citations: list[str],
    confidence: tuple[float, float],
    structured: dict[str, Any] | None = None,
    summary_contains: list[str] | None = None,
    missing_information: list[str] | None = None,
    expect_missing_evidence: bool = False,
    tags: list[str] | None = None,
) -> BenchmarkCase:
    return BenchmarkCase(
        case_id=case_id,
        skill_id=skill_id,
        dataset_id=dataset_id,
        dataset_version=_VERSION,
        task=task,
        evidence=tuple(ExpectedEvidence(et, rid) for et, rid in evidence),
        gold=GoldStandard(
            findings=tuple(findings),
            citations=tuple(citations),
            confidence_min=confidence[0],
            confidence_max=confidence[1],
            structured_fields=dict(structured or {}),
            missing_information=tuple(missing_information or ()),
            summary_contains=tuple(summary_contains or ()),
            expect_missing_evidence=expect_missing_evidence,
        ),
        tags=tuple(tags or ()),
    )


def _ds(
    dataset_id: str,
    skill_id: str,
    title: str,
    cases: list[BenchmarkCase],
    description: str,
) -> BenchmarkDataset:
    return BenchmarkDataset(
        dataset_id=dataset_id,
        version=_VERSION,
        skill_id=skill_id,
        title=title,
        cases=tuple(cases),
        description=description,
    )


BUILTIN_DATASETS: tuple[BenchmarkDataset, ...] = (
    _ds(
        "vehicle_damage_v1",
        "vehicle_damage_assessment",
        "Vehicle Damage",
        [
            _case(
                "vd-001",
                "vehicle_damage_assessment",
                "vehicle_damage_v1",
                task="Assess front-end collision damage from photos",
                evidence=[("vehicle_photos", "ev-vehicle-front-001")],
                findings=["front bumper damage", "hood crease"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={"severity": "moderate", "damage_locations": ["front bumper", "hood"]},
                summary_contains=["front", "damage"],
                tags=["builtin", "vision"],
            ),
            _case(
                "vd-missing",
                "vehicle_damage_assessment",
                "vehicle_damage_v1",
                task="Assess damage with no photos",
                evidence=[],
                findings=[],
                citations=[],
                confidence=(0.0, 0.4),
                expect_missing_evidence=True,
                tags=["builtin", "fail_closed"],
            ),
        ],
        "Gold cases for vehicle damage assessment.",
    ),
    _ds(
        "policy_review_v1",
        "policy_compliance_review",
        "Policy Review",
        [
            _case(
                "pr-001",
                "policy_compliance_review",
                "policy_review_v1",
                task="Review claim against coverage policy",
                evidence=[("policy_document", "ev-policy-001")],
                findings=["coverage applies to collision", "deductible clause present"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={
                    "compliance_status": "partial",
                    "findings": ["coverage applies to collision", "deductible clause present"],
                },
                summary_contains=["policy", "coverage"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for policy compliance review.",
    ),
    _ds(
        "contract_analysis_v1",
        "contract_analysis",
        "Contract Analysis",
        [
            _case(
                "ca-001",
                "contract_analysis",
                "contract_analysis_v1",
                task="Extract key obligations and risks",
                evidence=[("contract_document", "ev-contract-001")],
                findings=["payment due net 30", "indemnity clause favors vendor"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={
                    "parties": ["acme corp", "vendor llc"],
                    "risks": ["indemnity clause favors vendor"],
                },
                summary_contains=["contract", "obligation"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for contract analysis.",
    ),
    _ds(
        "budget_analysis_v1",
        "budget_analysis",
        "Budget Analysis",
        [
            _case(
                "ba-001",
                "budget_analysis",
                "budget_analysis_v1",
                task="Flag budget anomalies",
                evidence=[("budget_spreadsheet", "ev-budget-001")],
                findings=["line item exceeds category cap", "duplicate vendor payment"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={
                    "anomalies": ["line item exceeds category cap", "duplicate vendor payment"]
                },
                summary_contains=["budget", "anomal"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for budget analysis.",
    ),
    _ds(
        "timeline_v1",
        "timeline_construction",
        "Timeline",
        [
            _case(
                "tl-001",
                "timeline_construction",
                "timeline_v1",
                task="Build chronological event timeline",
                evidence=[("timeline_source", "ev-timeline-001")],
                findings=["incident reported", "adjuster assigned"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={"unresolved_gaps": ["exact time of impact unknown"]},
                summary_contains=["timeline"],
                missing_information=["exact time of impact unknown"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for timeline construction.",
    ),
    _ds(
        "evidence_summary_v1",
        "evidence_summary",
        "Evidence Summary",
        [
            _case(
                "es-001",
                "evidence_summary",
                "evidence_summary_v1",
                task="Summarize evidence bundle themes",
                evidence=[("evidence_bundle", "ev-bundle-001")],
                findings=["collision theme", "coverage dispute theme"],
                citations=["EV-001"],
                confidence=(0.35, 0.55),
                structured={"themes": ["collision theme", "coverage dispute theme"]},
                summary_contains=["evidence", "theme"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for evidence summary.",
    ),
    _ds(
        "document_comparison_v1",
        "document_comparison",
        "Document Comparison",
        [
            _case(
                "dc-001",
                "document_comparison",
                "document_comparison_v1",
                task="Compare two related documents",
                evidence=[
                    ("document_pair", "ev-doc-a-001"),
                    ("document_pair", "ev-doc-b-001"),
                ],
                findings=["dates disagree", "party names match"],
                citations=["EV-001", "EV-002"],
                confidence=(0.35, 0.55),
                structured={
                    "differences": ["dates disagree"],
                    "agreements": ["party names match"],
                },
                summary_contains=["compar"],
                tags=["builtin"],
            ),
        ],
        "Gold cases for document comparison.",
    ),
)


def register_builtin_datasets(registry: DatasetRegistry | None = None) -> None:
    reg = registry if registry is not None else DATASET_REGISTRY
    for ds in BUILTIN_DATASETS:
        reg.register(ds)


# Auto-register on import for default process registry.
register_builtin_datasets()
