"""Deterministic scoring for investigation skill outputs."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

from cobra_core.benchmark.config import BenchmarkConfig
from cobra_core.benchmark.schemas import (
    BenchmarkCase,
    BenchmarkExecution,
    CalibrationBin,
    CaseScore,
    CitationScore,
    GoldStandard,
)
from cobra_core.isf.schemas import validate_skill_output

_WS = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    return _WS.sub(" ", (value or "").strip().lower())


def _token_set(items: list[str] | tuple[str, ...]) -> set[str]:
    return {normalize_text(x) for x in items if normalize_text(x)}


def finding_scores(
    actual: list[str] | tuple[str, ...], expected: tuple[str, ...]
) -> tuple[float, float, float]:
    """Return (accuracy/F1, false_positive_rate, false_negative_rate)."""
    a = _token_set(actual)
    e = _token_set(expected)
    if not e and not a:
        return 1.0, 0.0, 0.0
    if not e:
        # No expected findings: any invented finding is FP.
        return (0.0 if a else 1.0), (1.0 if a else 0.0), 0.0
    tp = len(a & e)
    fp = len(a - e)
    fn = len(e - a)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (tp + fp) if (tp + fp) else 0.0
    fnr = fn / (tp + fn) if (tp + fn) else 0.0
    return round(f1, 4), round(fpr, 4), round(fnr, 4)


def score_citations(
    actual: list[str] | tuple[str, ...], expected: tuple[str, ...]
) -> CitationScore:
    a_list = [normalize_text(x) for x in actual if normalize_text(x)]
    e_set = _token_set(expected)
    counts = Counter(a_list)
    duplicate = sum(c - 1 for c in counts.values() if c > 1)
    unique = set(a_list)
    supported = len(unique & e_set)
    incorrect = len(unique - e_set)
    missing = len(e_set - unique)
    # Unsupported = present but not in gold (same as incorrect for this rubric).
    unsupported = incorrect
    denom = max(len(e_set), 1)
    accuracy = supported / denom
    if e_set and not unique:
        accuracy = 0.0
    elif not e_set and not unique:
        accuracy = 1.0
    elif not e_set and unique:
        accuracy = 0.0
    # Penalize duplicates lightly.
    accuracy = max(0.0, accuracy - 0.05 * duplicate)
    return CitationScore(
        supported=supported,
        unsupported=unsupported,
        incorrect=incorrect,
        missing=missing,
        duplicate=duplicate,
        accuracy=round(accuracy, 4),
    )


def schema_validity(skill_id: str, output: dict[str, Any], expect_valid: bool) -> float:
    try:
        validate_skill_output(skill_id, output)
        valid = True
    except Exception:
        valid = False
    if expect_valid:
        return 1.0 if valid else 0.0
    return 1.0 if not valid else 0.5


def completeness_score(output: dict[str, Any], gold: GoldStandard) -> float:
    scores: list[float] = []
    summary = normalize_text(str(output.get("summary") or ""))
    if gold.summary_contains:
        hits = sum(1 for frag in gold.summary_contains if normalize_text(frag) in summary)
        scores.append(hits / len(gold.summary_contains))
    for key, expected in gold.structured_fields.items():
        actual = output.get(key)
        if isinstance(expected, list):
            a_set = _token_set([str(x) for x in (actual or [])])
            e_set = _token_set([str(x) for x in expected])
            if not e_set:
                scores.append(1.0)
            else:
                scores.append(len(a_set & e_set) / len(e_set))
        else:
            scores.append(1.0 if normalize_text(str(actual)) == normalize_text(str(expected)) else 0.0)
    if gold.missing_information:
        actual_missing = _token_set([str(x) for x in (output.get("missing_information") or [])])
        expected_missing = _token_set(gold.missing_information)
        scores.append(len(actual_missing & expected_missing) / len(expected_missing))
    if not scores:
        return 1.0
    return round(sum(scores) / len(scores), 4)


def confidence_calibration_score(
    confidence: float, gold: GoldStandard, *, findings_correct: bool
) -> float:
    """
    Score whether reported confidence matches correctness and gold range.
    High confidence + incorrect → low; low confidence + correct → moderate.
    """
    in_range = gold.confidence_min - 1e-9 <= confidence <= gold.confidence_max + 1e-9
    range_score = 1.0 if in_range else 0.0
    if confidence >= 0.7:
        calib = 1.0 if findings_correct else 0.0
    elif confidence <= 0.4:
        calib = 0.8 if not findings_correct else 0.6
    else:
        calib = 0.7 if findings_correct else 0.4
    return round(0.5 * range_score + 0.5 * calib, 4)


def extract_findings(output: dict[str, Any]) -> list[str]:
    for key in (
        "findings",
        "damage_locations",
        "anomalies",
        "themes",
        "patterns",
        "risks",
        "obligations",
        "key_terms",
    ):
        val = output.get(key)
        if isinstance(val, list) and val:
            return [str(x) for x in val]
    # Document comparison: merge differences + agreements as finding set.
    diffs = output.get("differences")
    agrees = output.get("agreements")
    if isinstance(diffs, list) or isinstance(agrees, list):
        merged: list[str] = []
        if isinstance(diffs, list):
            merged.extend(str(x) for x in diffs)
        if isinstance(agrees, list):
            merged.extend(str(x) for x in agrees)
        if merged:
            return merged
    events = output.get("events")
    if isinstance(events, list):
        out: list[str] = []
        for ev in events:
            if isinstance(ev, dict):
                out.append(str(ev.get("label") or ev.get("description") or ev))
            else:
                out.append(str(ev))
        return out
    return []


def score_case(
    case: BenchmarkCase,
    execution: BenchmarkExecution,
    config: BenchmarkConfig,
) -> CaseScore:
    output = execution.output if isinstance(execution.output, dict) else {}
    gold = case.gold

    if gold.expect_missing_evidence:
        # Fail-closed path: credit detecting missing evidence / typed error.
        detected = bool(execution.error_code == "missing_required_evidence") or bool(
            output.get("missing_information")
        )
        overall = 1.0 if detected else 0.0
        cite = CitationScore(accuracy=1.0 if detected else 0.0)
        return CaseScore(
            case_id=case.case_id,
            skill_id=case.skill_id,
            provider_id=execution.provider_id,
            overall=overall,
            finding_accuracy=overall,
            citation_accuracy=cite.accuracy,
            schema_validity=1.0,
            completeness=overall,
            confidence_calibration=1.0 if detected else 0.0,
            false_positive_rate=0.0,
            false_negative_rate=0.0 if detected else 1.0,
            latency_ms=execution.latency_ms,
            estimated_cost_usd=execution.estimated_cost_usd,
            human_agreement=execution.human_agreement,
            citation=cite,
            passed=overall >= config.pass_threshold,
            details={"mode": "missing_evidence", "detected": detected},
        )

    findings = extract_findings(output)
    finding_acc, fpr, fnr = finding_scores(findings, gold.findings)
    citations = [str(x) for x in (output.get("citations") or [])]
    cite = score_citations(citations, gold.citations)
    schema = schema_validity(case.skill_id, output, gold.expect_schema_valid)
    complete = completeness_score(output, gold)
    conf = float(output.get("confidence") or 0.0)
    findings_ok = finding_acc >= 0.7
    calib = confidence_calibration_score(conf, gold, findings_correct=findings_ok)

    weights = [
        (config.weight_finding_accuracy, finding_acc),
        (config.weight_citation_accuracy, cite.accuracy),
        (config.weight_schema_validity, schema),
        (config.weight_completeness, complete),
        (config.weight_confidence_calibration, calib),
    ]
    wsum = sum(w for w, _ in weights) or 1.0
    overall = round(sum(w * s for w, s in weights) / wsum, 4)
    if execution.human_agreement is not None:
        overall = round(0.9 * overall + 0.1 * max(0.0, min(1.0, execution.human_agreement)), 4)

    return CaseScore(
        case_id=case.case_id,
        skill_id=case.skill_id,
        provider_id=execution.provider_id,
        overall=overall,
        finding_accuracy=finding_acc,
        citation_accuracy=cite.accuracy,
        schema_validity=schema,
        completeness=complete,
        confidence_calibration=calib,
        false_positive_rate=fpr,
        false_negative_rate=fnr,
        latency_ms=execution.latency_ms,
        estimated_cost_usd=execution.estimated_cost_usd,
        human_agreement=execution.human_agreement,
        citation=cite,
        passed=overall >= config.pass_threshold,
        details={
            "confidence": conf,
            "findings_actual": findings,
            "citations_actual": citations,
        },
    )


def build_calibration_curve(scores: list[CaseScore], executions: list[BenchmarkExecution]) -> tuple[CalibrationBin, ...]:
    by_case = {e.case_id: e for e in executions}
    bins = {
        "high": {"count": 0, "correct": 0},
        "medium": {"count": 0, "correct": 0},
        "low": {"count": 0, "correct": 0},
    }
    for sc in scores:
        ex = by_case.get(sc.case_id)
        conf = float((ex.output if ex else {}).get("confidence") or 0.0) if ex else 0.0
        label = "high" if conf >= 0.7 else ("low" if conf <= 0.4 else "medium")
        bins[label]["count"] += 1
        if sc.finding_accuracy >= 0.7:
            bins[label]["correct"] += 1
    out: list[CalibrationBin] = []
    for label in ("high", "medium", "low"):
        c = bins[label]["count"]
        ok = bins[label]["correct"]
        out.append(
            CalibrationBin(
                label=label,
                count=c,
                correct=ok,
                accuracy=round(ok / c, 4) if c else 0.0,
            )
        )
    return tuple(out)
