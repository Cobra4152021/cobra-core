"""Static validation for CobraBench v0.2 release candidates."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from cobra_core.evaluators.registry import load_evaluator_metadata
from cobra_core.prompts.registry import load_prompt_template
from cobra_core.runtime_policies.loader import load_runtime_profile
from cobra_core.schemas.benchmark_v02 import BenchmarkCaseV02
from cobra_core.schemas.categories import CATEGORY_WEIGHTS_V02, BenchmarkCategory

ANSWER_CUE = re.compile(
    r"\b(the correct answer is|reference answer:|gold answer)\b",
    re.IGNORECASE,
)


def load_v02_cases(cases_dir: Path) -> list[BenchmarkCaseV02]:
    cases = [
        BenchmarkCaseV02.model_validate_json(p.read_text(encoding="utf-8"))
        for p in sorted(cases_dir.glob("*.json"))
    ]
    ids = [c.case_id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case_id in v0.2 cases")
    return cases


def validate_v02_case(case: BenchmarkCaseV02, *, repo_root: Path) -> list[str]:
    errors: list[str] = []
    keys = [s.citation_key for s in case.supporting_sources]
    if len(keys) != len(set(keys)):
        errors.append(f"{case.case_id}: duplicate source keys")

    if case.material_evidence and keys:
        referenced = (
            case.material_evidence.required_evidence_ids
            + case.material_evidence.optional_evidence_ids
            + case.material_evidence.contrary_evidence_ids
        )
        for key in referenced:
            if key not in keys:
                errors.append(f"{case.case_id}: unknown evidence id {key}")

    if case.difficulty_level < 1 or case.difficulty_level > 5:
        errors.append(f"{case.case_id}: invalid difficulty")

    if case.prompt_template_id and case.prompt_template_version:
        try:
            load_prompt_template(
                case.prompt_template_id,
                case.prompt_template_version,
                repo_root=repo_root,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{case.case_id}: prompt template: {exc}")

    if case.output_budget and case.output_budget.runtime_profile_id:
        try:
            load_runtime_profile(
                case.output_budget.runtime_profile_id,
                repo_root=repo_root,
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{case.case_id}: runtime profile: {exc}")

    if case.evaluator_versions:
        mapping = case.evaluator_versions.model_dump(exclude_none=True)
        for name, ver in mapping.items():
            try:
                load_evaluator_metadata(name, ver, repo_root=repo_root)
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{case.case_id}: evaluator {name}@{ver}: {exc}")

    if case.format_expectations and case.format_expectations.parser_mode not in {
        "strict",
        "tolerant",
        "both",
    }:
        errors.append(f"{case.case_id}: invalid parser mode")

    if not case.expected_behaviors:
        errors.append(f"{case.case_id}: missing expected behaviors")

    if ANSWER_CUE.search(case.user_prompt) or ANSWER_CUE.search(case.system_prompt):
        errors.append(f"{case.case_id}: answer cue in prompt")

    if case.human_review and case.human_review.unresolved_ambiguity:
        errors.append(f"{case.case_id}: unresolved ambiguity blocks release")

    if case.status == "release_candidate" and (
        case.human_review is None or case.human_review.approval_status != "approved"
    ):
        errors.append(f"{case.case_id}: not approved for rc")

    return errors


def validate_v02_suite(cases_dir: Path, *, repo_root: Path) -> list[str]:
    errors: list[str] = []
    cases = load_v02_cases(cases_dir)
    for case in cases:
        errors.extend(validate_v02_case(case, repo_root=repo_root))

    dist = Counter(c.category for c in cases)
    expected = {
        BenchmarkCategory.INVESTIGATION_REASONING: 6,
        BenchmarkCategory.EVIDENCE_GROUNDING: 6,
        BenchmarkCategory.HALLUCINATION_RESISTANCE: 5,
        BenchmarkCategory.CITATION_CORRECTNESS: 5,
        BenchmarkCategory.CONTRADICTION_DETECTION: 6,
        BenchmarkCategory.CODING: 4,
        BenchmarkCategory.LONG_DOCUMENT_ANALYSIS: 4,
        BenchmarkCategory.REFUSAL_QUALITY: 3,
        BenchmarkCategory.INSTRUCTION_FOLLOWING: 4,
        BenchmarkCategory.UNCERTAINTY_CALIBRATION: 3,
    }
    for cat, n in expected.items():
        if dist.get(cat, 0) != n:
            errors.append(f"category distribution {cat.value}: got {dist.get(cat, 0)} want {n}")

    if abs(sum(CATEGORY_WEIGHTS_V02.values()) - 1.0) > 1e-9:
        errors.append("CATEGORY_WEIGHTS_V02 must sum to 1.0")

    if not (40 <= len(cases) <= 48):
        errors.append(f"case count {len(cases)} outside 40–48")

    # Near-duplicate titles
    titles = [c.title.lower().strip() for c in cases]
    if len(titles) != len(set(titles)):
        errors.append("duplicate titles detected")

    return errors


def category_distribution(cases: list[BenchmarkCaseV02]) -> dict[str, int]:
    return {k.value: v for k, v in sorted(Counter(c.category for c in cases).items())}


def difficulty_distribution(cases: list[BenchmarkCaseV02]) -> dict[str, int]:
    return {str(k): v for k, v in sorted(Counter(c.difficulty_level for c in cases).items())}


def suite_summary(cases_dir: Path) -> dict[str, Any]:
    cases = load_v02_cases(cases_dir)
    return {
        "case_count": len(cases),
        "categories": category_distribution(cases),
        "difficulty": difficulty_distribution(cases),
        "synthetic_count": sum(1 for c in cases if c.contamination and c.contamination.synthetic),
        "approved_count": sum(
            1 for c in cases if c.human_review and c.human_review.approval_status == "approved"
        ),
    }
