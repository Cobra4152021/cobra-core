"""Typed contracts for benchmark datasets, executions, and scores."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ExpectedEvidence:
    evidence_type: str
    ref_id: str


@dataclass(frozen=True)
class GoldStandard:
    """Versioned expected outcomes for one case."""

    findings: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    confidence_min: float = 0.0
    confidence_max: float = 1.0
    # Keys that must be present with matching values (skill-specific).
    structured_fields: dict[str, Any] = field(default_factory=dict)
    # Strings that should appear in missing_information when incomplete.
    missing_information: tuple[str, ...] = ()
    # Gold answer summary fragments (substring match, normalized).
    summary_contains: tuple[str, ...] = ()
    expect_schema_valid: bool = True
    # If true, case expects missing required evidence / fail-closed path.
    expect_missing_evidence: bool = False


@dataclass(frozen=True)
class BenchmarkCase:
    case_id: str
    skill_id: str
    dataset_id: str
    dataset_version: str
    task: str
    evidence: tuple[ExpectedEvidence, ...]
    gold: GoldStandard
    tags: tuple[str, ...] = ()
    notes: str = ""


@dataclass(frozen=True)
class BenchmarkDataset:
    dataset_id: str
    version: str
    skill_id: str
    title: str
    cases: tuple[BenchmarkCase, ...]
    description: str = ""

    def __post_init__(self) -> None:
        if not self.dataset_id or not self.version:
            raise ValueError("dataset_id and version are required")
        if not self.cases:
            raise ValueError("dataset must contain at least one case")


@dataclass
class BenchmarkExecution:
    """Observed skill execution result (isolated; not production history)."""

    case_id: str
    skill_id: str
    provider_id: str
    workflow_id: str
    output: dict[str, Any]
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    status: str = "completed"
    error_code: str = ""
    # Optional human rater agreement score in [0, 1] when available.
    human_agreement: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CitationScore:
    supported: int = 0
    unsupported: int = 0
    incorrect: int = 0
    missing: int = 0
    duplicate: int = 0
    accuracy: float = 0.0


@dataclass(frozen=True)
class CalibrationBin:
    label: str
    count: int
    correct: int
    accuracy: float


@dataclass(frozen=True)
class CaseScore:
    case_id: str
    skill_id: str
    provider_id: str
    overall: float
    finding_accuracy: float
    citation_accuracy: float
    schema_validity: float
    completeness: float
    confidence_calibration: float
    false_positive_rate: float
    false_negative_rate: float
    latency_ms: float
    estimated_cost_usd: float
    human_agreement: float | None
    citation: CitationScore
    passed: bool
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepeatabilityResult:
    case_id: str
    runs: int
    identical_output_rate: float
    score_variance: float
    confidence_variance: float
    citation_variance: float


@dataclass(frozen=True)
class BenchmarkRunResult:
    run_id: str
    dataset_id: str
    dataset_version: str
    provider_id: str
    workflow_id: str
    case_scores: tuple[CaseScore, ...]
    overall_score: float
    passed: bool
    latency_avg_ms: float
    cost_total_usd: float
    calibration_curve: tuple[CalibrationBin, ...]
    repeatability: tuple[RepeatabilityResult, ...] = ()
    recommendations: tuple[str, ...] = ()
