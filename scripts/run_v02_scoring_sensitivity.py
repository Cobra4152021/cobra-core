#!/usr/bin/env python3
"""Phase 2H scoring-sensitivity fixture runner (no model)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobra_core.evaluators.citations.v2 import evaluate_citations_v2  # noqa: E402
from cobra_core.evaluators.contradictions.v2 import evaluate_contradictions_v2  # noqa: E402
from cobra_core.evaluators.format_compliance.v2 import evaluate_format_compliance_v2  # noqa: E402
from cobra_core.evaluators.unsupported_claims.v2 import evaluate_unsupported_claims_v2  # noqa: E402

FIXTURES = ROOT / "evaluations/fixtures/cobrabench-v0.2-rc2-scoring-sensitivity/fixtures.json"
OUT = ROOT / "evaluations/fixtures/cobrabench-v0.2-rc2-scoring-sensitivity/results.json"


def main() -> int:
    data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    results = []
    failures: list[str] = []
    family_scores: dict[str, list[tuple[int, float]]] = {}

    for fix in data["fixtures"]:
        fid = fix["fixture_id"]
        exp = fix["expect"]
        family = fix["family"]
        rank = fix["quality_rank"]
        status = "ok"
        detail: dict = {"fixture_id": fid, "family": family, "quality_rank": rank}
        score = 0.0

        if family == "format":
            fmt = evaluate_format_compliance_v2(fix["response"])
            score = fmt.semantic_score
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
            if "strict_parse" in exp and fmt.parse_success != exp["strict_parse"]:
                status = "fail"
            if "tolerant_parse" in exp and fmt.tolerant_parse_success != exp["tolerant_parse"]:
                status = "fail"
        elif family == "citation":
            cit = evaluate_citations_v2(
                fix["response"],
                allowed_keys=fix["allowed_keys"],
                required_evidence_ids=fix["required_evidence_ids"],
            )
            score = (cit.citation_precision + cit.evidence_coverage) / 2
            detail["citation"] = {
                "precision": cit.citation_precision,
                "evidence_coverage": cit.evidence_coverage,
            }
            if cit.citation_precision < exp.get("citation_precision_min", 0):
                status = "fail"
            if cit.evidence_coverage < exp.get("evidence_coverage_min", 0):
                status = "fail"
            if cit.evidence_coverage > exp.get("evidence_coverage_max", 1):
                status = "fail"
        elif family == "contradiction":
            c = evaluate_contradictions_v2(fix["response"])
            score = c.detection
            detail["contradiction"] = {
                "detection": c.detection,
                "resolution": c.resolution_evidence_recommendation,
            }
            if c.detection < exp.get("detection_min", 0):
                status = "fail"
            if c.detection > exp.get("detection_max", 1):
                status = "fail"
            if c.resolution_evidence_recommendation < exp.get("resolution_min", 0):
                status = "fail"
        elif family == "unsupported":
            uc = evaluate_unsupported_claims_v2(
                fix["response"],
                fix.get("allowed_keys", []),
                fix.get("sources"),
            )
            # Prefer uncertain+flag signal: grounded answers score higher than uncertain novel claims.
            score = (
                1.0
                if uc.unsupported_flag_count == 0 and uc.uncertain_count == 0
                else (0.5 if uc.uncertain_count and uc.unsupported_flag_count == 0 else 0.0)
            )
            detail["unsupported"] = {
                "flags": uc.unsupported_flag_count,
                "uncertain": uc.uncertain_count,
            }
            if uc.unsupported_flag_count > exp.get("unsupported_flag_max", 10**9):
                status = "fail"
            if uc.unsupported_flag_count < exp.get("unsupported_flag_min", 0):
                status = "fail"
            if uc.uncertain_count < exp.get("uncertain_min", 0):
                status = "fail"

        detail["status"] = status
        detail["score"] = score
        results.append(detail)
        family_scores.setdefault(family, []).append((rank, score))
        if status != "ok":
            failures.append(fid)

    ordering_ok = True
    ordering_notes = []
    for family, pairs in family_scores.items():
        ordered = sorted(pairs, key=lambda x: x[0])
        scores = [s for _, s in ordered]
        # Non-increasing quality rank should not have strictly increasing badness ignored:
        # lower rank number should have score >= later ranks (allow ties).
        for i in range(len(scores) - 1):
            # Flag clear inversions where better rank scored worse by >0.05.
            if ordered[i][0] < ordered[i + 1][0] and scores[i] + 0.05 < scores[i + 1]:
                ordering_ok = False
                ordering_notes.append(f"{family}: rank inversion {ordered[i]} vs {ordered[i + 1]}")

    payload = {
        "ok": not failures and ordering_ok,
        "failures": failures,
        "ordering_ok": ordering_ok,
        "ordering_notes": ordering_notes,
        "results": results,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {"ok": payload["ok"], "failures": failures, "ordering_ok": ordering_ok}, indent=2
        )
    )
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
