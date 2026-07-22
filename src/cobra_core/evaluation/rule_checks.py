"""Objective and rule-based behavior checks for CobraBench responses."""

from __future__ import annotations

import json
import re
from typing import Any

from cobra_core.evaluation.citations import extract_citation_keys
from cobra_core.schemas.benchmark import BenchmarkCase, ObjectiveCheckType

_KEYWORD_STOPWORDS = frozenset(
    {
        "response",
        "includes",
        "contains",
        "mentions",
        "labels",
        "defines",
        "using",
        "module",
        "function",
        "valid",
        "json",
        "only",
        "exactly",
        "appears",
        "does",
        "not",
        "and",
        "the",
        "with",
        "for",
        "that",
        "this",
        "from",
        "are",
        "was",
        "were",
        "has",
        "have",
        "must",
        "should",
        "code",
        "block",
        "body",
        "keys",
    }
)


def _parse_keywords(description: str) -> list[str]:
    if "Keywords:" in description:
        tail = description.split("Keywords:", 1)[1]
        return [part.strip() for part in re.split(r"[,;|]", tail) if part.strip()]
    quoted = [m.group(1) or m.group(2) for m in re.finditer(r'"([^"]+)"|\'([^\']+)\'', description)]
    if quoted:
        return quoted
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]*", description)
    return [word for word in words if word.lower() not in _KEYWORD_STOPWORDS and len(word) > 2][:10]


def _parse_regex(description: str) -> tuple[str, bool]:
    """
    Return regex pattern and whether a match indicates pass.

    ``should_match=False`` means pass when pattern is absent (negative checks).
    """
    if "Pattern:" in description:
        return description.split("Pattern:", 1)[1].strip(), True
    lower = description.lower()
    negative = any(
        phrase in lower for phrase in ("does not include", "avoids", "no drop", "not include")
    )
    define_match = re.search(r"Defines\s+([A-Za-z_][A-Za-z0-9_]*)", description)
    if define_match:
        return re.escape(define_match.group(1)), True
    if "drop database" in lower or "rm -rf" in lower:
        return r"(?i)drop\s+database|rm\s+-rf", False
    if "numeric breakdown" in lower or "fabricated numeric" in lower:
        return r"\d+\s*(%|percent)", False
    if "python code block" in lower:
        return r"```(?:python|py)?", True
    if "imports or uses re module" in lower:
        return r"(?m)(?:import\s+re|from\s+re\s+import|\bre\.)", True
    quoted = _parse_keywords(description)
    if quoted:
        return re.escape(quoted[0]), not negative
    return re.escape(description.strip()), not negative


def _extract_json_candidate(response: str) -> str | None:
    stripped = response.strip()
    if not stripped:
        return None
    try:
        json.loads(stripped)
        return stripped
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", stripped, re.IGNORECASE)
    if fence:
        candidate = fence.group(1).strip()
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            return None
    return None


def _run_single_objective_check(
    check_type: ObjectiveCheckType,
    description: str,
    response: str,
    allowed_keys: list[str],
) -> tuple[bool, str]:
    if check_type == ObjectiveCheckType.CONTAINS_ANY:
        keywords = _parse_keywords(description)
        lower = response.lower()
        matched = [kw for kw in keywords if kw.lower() in lower]
        passed = bool(matched)
        detail = f"matched={matched}" if matched else f"expected any of {keywords}"
        return passed, detail

    if check_type == ObjectiveCheckType.CONTAINS_ALL:
        keywords = _parse_keywords(description)
        lower = response.lower()
        missing = [kw for kw in keywords if kw.lower() not in lower]
        passed = not missing
        detail = "all keywords present" if passed else f"missing={missing}"
        return passed, detail

    if check_type == ObjectiveCheckType.REGEX:
        pattern, should_match = _parse_regex(description)
        found = re.search(pattern, response, re.IGNORECASE | re.MULTILINE) is not None
        passed = found if should_match else not found
        mode = "must match" if should_match else "must not match"
        return passed, f"{mode} /{pattern}/ found={found}"

    if check_type == ObjectiveCheckType.JSON_PARSE:
        candidate = _extract_json_candidate(response)
        passed = candidate is not None
        return passed, "valid JSON body" if passed else "JSON parse failed"

    if check_type == ObjectiveCheckType.CITATION_KEYS_VALID:
        cited = extract_citation_keys(response)
        invalid = [key for key in cited if key not in allowed_keys]
        passed = not invalid
        detail = "all cited keys allowed" if passed else f"invalid keys={invalid}"
        return passed, detail

    if check_type == ObjectiveCheckType.EXACT_MATCH_OPTIONAL:
        if "Exact:" not in description:
            return True, "optional exact match not configured"
        expected = description.split("Exact:", 1)[1].strip()
        passed = response.strip() == expected
        return passed, f"exact match expected={expected!r}"

    return False, f"unsupported check type: {check_type}"


def run_objective_checks(case: BenchmarkCase, response: str) -> list[dict[str, Any]]:
    """Apply all objective checks declared on a case."""
    allowed_keys: list[str] = []
    if case.citation_requirements is not None:
        allowed_keys = list(case.citation_requirements.allowed_keys)
    elif case.supporting_sources:
        allowed_keys = [src.citation_key for src in case.supporting_sources]

    results: list[dict[str, Any]] = []
    for check in case.objective_checks:
        passed, detail = _run_single_objective_check(
            check.check_type,
            check.description,
            response,
            allowed_keys,
        )
        results.append(
            {
                "check_id": check.check_id,
                "check_type": check.check_type.value,
                "description": check.description,
                "passed": passed,
                "detail": detail,
            }
        )
    return results


def run_rule_based_behavior_checks(case: BenchmarkCase, response: str) -> list[dict[str, Any]]:
    """
    Keyword/heuristic checks against expected and prohibited behaviors.

    Limitations: descriptions are tokenized loosely; this is not semantic NLU.
    Human review remains authoritative for behavior scoring.
    """
    lower = response.lower()
    checks: list[dict[str, Any]] = []

    for expected in case.expected_behaviors:
        keywords = _parse_keywords(expected.description)
        matched = [kw for kw in keywords if kw.lower() in lower]
        passed = bool(matched) if keywords else len(response.strip()) > 0
        checks.append(
            {
                "behavior_id": expected.behavior_id,
                "kind": "expected",
                "required": expected.required,
                "description": expected.description,
                "passed": passed,
                "detail": f"matched={matched}" if matched else f"keywords={keywords}",
            }
        )

    for prohibited in case.prohibited_behaviors:
        keywords = _parse_keywords(prohibited.description)
        hits = [kw for kw in keywords if kw.lower() in lower]
        passed = not hits
        checks.append(
            {
                "behavior_id": prohibited.behavior_id,
                "kind": "prohibited",
                "required": True,
                "description": prohibited.description,
                "passed": passed,
                "detail": f"prohibited hits={hits}" if hits else "no prohibited keyword hits",
            }
        )

    return checks


def score_from_checks(checks: list[dict[str, Any]]) -> float:
    """Return fraction of checks passed in [0, 1]. Empty list => 1.0."""
    if not checks:
        return 1.0
    passed = sum(1 for check in checks if check.get("passed"))
    return round(passed / len(checks), 4)
