"""Diagnostic cohort validation (separate from CobraBench v0.1)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

REQUIRED_COHORTS = (
    "A_output_cap",
    "B_thinking",
    "C_prompt_format",
    "D_evidence_delimiters",
    "E_stability",
)


class DiagnosticSuiteError(Exception):
    """Invalid diagnostic suite definition."""


class DiagnosticCohort(BaseModel):
    model_config = ConfigDict(extra="allow")

    variable: str
    values: list[Any]
    cases: list[str]
    hold_constant: list[str] = Field(default_factory=list)


class DiagnosticSuite(BaseModel):
    model_config = ConfigDict(extra="allow")

    suite_id: str
    suite_version: str
    not_cobrabench: bool
    baseline_run_id: str
    max_generations_budget: int
    cohorts: dict[str, DiagnosticCohort]
    planned_generation_count: int | None = None


def load_diagnostic_suite(path: Path | str) -> DiagnosticSuite:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return DiagnosticSuite.model_validate(data)


def validate_diagnostic_suite(suite: DiagnosticSuite) -> list[str]:
    """Validate cohort completeness and separation from CobraBench."""
    errors: list[str] = []
    if suite.not_cobrabench is not True:
        errors.append("Diagnostic suite must set not_cobrabench=true")
    if "cobrabench" in suite.suite_id.lower() and "phase-2e" not in suite.suite_id.lower():
        errors.append("Diagnostic suite_id must not claim to be CobraBench v0.1")
    for name in REQUIRED_COHORTS:
        if name not in suite.cohorts:
            errors.append(f"Missing required cohort: {name}")
    for name, cohort in suite.cohorts.items():
        if not cohort.cases:
            errors.append(f"Cohort {name} has no cases")
        if not cohort.values:
            errors.append(f"Cohort {name} has no values")
        if not cohort.variable:
            errors.append(f"Cohort {name} missing variable")
    if (
        suite.planned_generation_count is not None
        and suite.planned_generation_count > suite.max_generations_budget
    ):
        errors.append(
            f"planned_generation_count {suite.planned_generation_count} "
            f"exceeds budget {suite.max_generations_budget}"
        )
    return errors


def assert_diagnostic_run_separated(
    diagnostic_run_id: str,
    *,
    baseline_run_id: str,
    diagnostic_root: Path | str,
    baseline_root: Path | str,
) -> None:
    """Refuse diagnostic runs that reuse or overwrite the official baseline path."""
    if diagnostic_run_id == baseline_run_id:
        raise DiagnosticSuiteError("Diagnostic run_id must differ from official baseline run_id")
    diag = Path(diagnostic_root).resolve()
    base = Path(baseline_root).resolve()
    if diag == base:
        raise DiagnosticSuiteError(
            "Diagnostic output directory must not equal locked baseline directory"
        )
    if base in diag.parents:
        raise DiagnosticSuiteError(
            "Diagnostic output must not be nested under the locked baseline run"
        )
