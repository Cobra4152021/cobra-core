"""Dataset loading and validation."""

from __future__ import annotations

from typing import Any

from cobra_core.benchmark.schemas import (
    BenchmarkCase,
    BenchmarkDataset,
    ExpectedEvidence,
    GoldStandard,
)


def _norm_str_list(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise ValueError("expected list of strings")
    out: list[str] = []
    for item in value:
        s = str(item).strip()
        if s:
            out.append(s)
    return tuple(out)


def case_from_dict(raw: dict[str, Any], *, dataset_id: str, dataset_version: str) -> BenchmarkCase:
    if not isinstance(raw, dict):
        raise ValueError("case must be an object")
    case_id = str(raw.get("case_id") or "").strip()
    skill_id = str(raw.get("skill_id") or "").strip()
    if not case_id or not skill_id:
        raise ValueError("case_id and skill_id are required")
    evidence_raw = raw.get("evidence") or []
    if not isinstance(evidence_raw, list):
        raise ValueError("evidence must be a list")
    evidence: list[ExpectedEvidence] = []
    for item in evidence_raw:
        if not isinstance(item, dict):
            raise ValueError("evidence item must be an object")
        et = str(item.get("evidence_type") or "").strip()
        rid = str(item.get("ref_id") or "").strip()
        if not et or not rid:
            raise ValueError("evidence requires evidence_type and ref_id")
        evidence.append(ExpectedEvidence(evidence_type=et, ref_id=rid))
    gold_raw = raw.get("gold") or {}
    if not isinstance(gold_raw, dict):
        raise ValueError("gold must be an object")
    conf_min = float(gold_raw.get("confidence_min", 0.0))
    conf_max = float(gold_raw.get("confidence_max", 1.0))
    if not 0.0 <= conf_min <= conf_max <= 1.0:
        raise ValueError("invalid confidence range")
    structured = gold_raw.get("structured_fields") or {}
    if not isinstance(structured, dict):
        raise ValueError("structured_fields must be an object")
    gold = GoldStandard(
        findings=_norm_str_list(gold_raw.get("findings")),
        citations=_norm_str_list(gold_raw.get("citations")),
        confidence_min=conf_min,
        confidence_max=conf_max,
        structured_fields=dict(structured),
        missing_information=_norm_str_list(gold_raw.get("missing_information")),
        summary_contains=_norm_str_list(gold_raw.get("summary_contains")),
        expect_schema_valid=bool(gold_raw.get("expect_schema_valid", True)),
        expect_missing_evidence=bool(gold_raw.get("expect_missing_evidence", False)),
    )
    tags = _norm_str_list(raw.get("tags"))
    return BenchmarkCase(
        case_id=case_id,
        skill_id=skill_id,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        task=str(raw.get("task") or "").strip(),
        evidence=tuple(evidence),
        gold=gold,
        tags=tags,
        notes=str(raw.get("notes") or ""),
    )


def dataset_from_dict(raw: dict[str, Any]) -> BenchmarkDataset:
    if not isinstance(raw, dict):
        raise ValueError("dataset must be an object")
    dataset_id = str(raw.get("dataset_id") or "").strip()
    version = str(raw.get("version") or "").strip()
    skill_id = str(raw.get("skill_id") or "").strip()
    title = str(raw.get("title") or dataset_id).strip()
    cases_raw = raw.get("cases") or []
    if not isinstance(cases_raw, list) or not cases_raw:
        raise ValueError("cases must be a non-empty list")
    cases = tuple(
        case_from_dict(c, dataset_id=dataset_id, dataset_version=version)
        for c in cases_raw
        if isinstance(c, dict)
    )
    if len(cases) != len(cases_raw):
        raise ValueError("every case must be an object")
    return BenchmarkDataset(
        dataset_id=dataset_id,
        version=version,
        skill_id=skill_id,
        title=title,
        cases=cases,
        description=str(raw.get("description") or ""),
    )


def validate_dataset(dataset: BenchmarkDataset) -> list[str]:
    """Return validation issues (empty = valid)."""
    issues: list[str] = []
    seen: set[str] = set()
    for case in dataset.cases:
        if case.case_id in seen:
            issues.append(f"duplicate case_id: {case.case_id}")
        seen.add(case.case_id)
        if case.skill_id != dataset.skill_id:
            issues.append(
                f"{case.case_id}: skill_id {case.skill_id!r} != dataset {dataset.skill_id!r}"
            )
        if case.dataset_version != dataset.version:
            issues.append(f"{case.case_id}: version mismatch")
        g = case.gold
        if not 0.0 <= g.confidence_min <= g.confidence_max <= 1.0:
            issues.append(f"{case.case_id}: bad confidence range")
        if not g.expect_missing_evidence and not case.evidence and not g.findings:
            issues.append(f"{case.case_id}: empty evidence and findings")
    return issues
