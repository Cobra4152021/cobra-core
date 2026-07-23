#!/usr/bin/env python3
"""Run authored scoring fixtures for CobraBench v0.2-rc1 evaluators (no model)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluators.citations.v2 import evaluate_citations_v2  # noqa: E402
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2  # noqa: E402
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2  # noqa: E402
from cobra_core.evaluators.telemetry.output_budget import (  # noqa: E402
    CompletionClass,
    classify_output_budget,
)
from cobra_core.evaluators.unsupported_claims.v2 import evaluate_unsupported_claims_v2  # noqa: E402

FIXTURES = ROOT / "evaluations/fixtures/cobrabench-v0.2-rc1-scoring/fixtures.json"
OUT = ROOT / "evaluations/fixtures/cobrabench-v0.2-rc1-scoring/results.json"


def main() -> int:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    results = []
    failures = []
    for fix in data["fixtures"]:
        fid = fix["fixture_id"]
        exp = fix["expect"]
        status = "ok"
        detail: dict = {"fixture_id": fid}

        if fid.startswith("fmt-"):
            fmt = evaluate_format_compliance_v2(fix["response"])
            detail["format"] = {
                "semantic": fmt.semantic_score,
                "exact": fmt.exact_format_score,
                "strict": fmt.parse_success,
                "tolerant": fmt.tolerant_parse_success,
            }
            if fmt.semantic_score < exp.get("format_semantic_min", 0):
                status = "fail"
            if fmt.semantic_score > exp.get("format_semantic_max", 1):
                status = "fail"
            if fmt.exact_format_score < exp.get("format_exact_min", 0):
                status = "fail"
            if fmt.exact_format_score > exp.get("format_exact_max", 1):
                status = "fail"
            if fmt.parse_success != exp.get("strict_parse", fmt.parse_success):
                status = "fail"
            if fmt.tolerant_parse_success != exp.get("tolerant_parse", fmt.tolerant_parse_success):
                status = "fail"

        elif fid.startswith("cite-"):
            cit = evaluate_citations_v2(
                fix["response"],
                allowed_keys=fix["allowed_keys"],
                required_evidence_ids=fix["required_evidence_ids"],
            )
            detail["citation"] = cit.model_dump()
            if cit.citation_precision < exp.get("citation_precision_min", 0):
                status = "fail"
            if cit.evidence_coverage < exp.get("evidence_coverage_min", 0):
                status = "fail"
            if cit.evidence_coverage > exp.get("evidence_coverage_max", 1):
                status = "fail"

        elif fid.startswith("contra-"):
            c = evaluate_contradictions_v2(fix["response"])
            detail["contradiction"] = c.model_dump()
            if c.detection < exp.get("detection_min", 0):
                status = "fail"
            if c.detection > exp.get("detection_max", 1):
                status = "fail"
            if c.numerical_comparison < exp.get("numerical_min", 0):
                status = "fail"
            if c.resolution_evidence_recommendation < exp.get("resolution_min", 0):
                status = "fail"

        elif fid.startswith("uc-"):
            uc = evaluate_unsupported_claims_v2(
                fix["response"],
                fix.get("allowed_keys", []),
                fix.get("sources"),
            )
            detail["unsupported"] = {
                "flags": uc.unsupported_flag_count,
                "uncertain": uc.uncertain_count,
            }
            if uc.unsupported_flag_count > exp.get("unsupported_flag_max", 0):
                status = "fail"

        elif fid.startswith("budget-"):
            b = classify_output_budget(
                response=fix["response"],
                requested_max_output_tokens=fix["requested_max_output_tokens"],
                actual_output_tokens=fix["actual_output_tokens"],
                finish_reason=fix["finish_reason"],
                required_sections=["KeyFacts", "Exceptions", "OpenQuestions"],
            )
            detail["budget"] = b.model_dump(mode="json")
            if (
                exp.get("not_budget_exhaustion")
                and b.completion_class == CompletionClass.LIKELY_BUDGET_EXHAUSTION
            ):
                status = "fail"
            if (
                exp.get("budget_exhaustion")
                and b.completion_class != CompletionClass.LIKELY_BUDGET_EXHAUSTION
            ):
                status = "fail"

        detail["status"] = status
        results.append(detail)
        if status != "ok":
            failures.append(fid)

    payload = {"ok": not failures, "failures": failures, "results": results}
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["ok"], "failures": failures}, indent=2))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
