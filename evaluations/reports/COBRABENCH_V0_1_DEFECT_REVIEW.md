# CobraBench v0.1 Defect Review (after Qwen3-8B interim run)

**Date:** 2026-07-22  
**Run:** `20260722T200000Z-8bba5e01`  
**Policy:** Frozen v0.1 was **not** modified after execution began.

## Findings

| Finding | Classification | Notes |
| --- | --- | --- |
| Automated unsupported-claim heuristic over-counts (172 “unsupported” across run) | scoring clarification | Rule layer useful as signal only; must not be treated as hallucination ground truth. Propose clearer claim-segmentation in v0.1.1 evaluator docs. |
| Automated hallucination classifier labeled many grounded answers H3 | scoring clarification / possible evaluator bias | Human layer corrected distribution to mostly H0. Keep severity human-authoritative for interim baseline. |
| Instruction case `cb-027` rewards exact line labels; model used markdown bullets with correct content | case defect requiring next version **or** scoring clarification | Consider accepting semantically equivalent section headers in v0.1.1 rubric notes; do not edit v0.1. |
| Long-document cases (`cb-023`, `cb-024`) are dense relative to 512-token cap | documentation improvement | Protocol max_new_tokens may truncate thorough answers; document as known limitation for v0.1. |
| Some hallucination cases omit `citation_requirements` when sources exist only as negative controls | no defect | Optional field; behavior covered by expected/prohibited behaviors. |
| Category counts match target distribution | no defect | 28 cases as frozen. |
| Keyword behavior checks are brittle | scoring clarification | Expected for v0.1; human review required. |
| Cases generally synthetic and free of private evidence | no defect | Aligns with contamination policy. |
| No accidental answer cue that invalidated the suite observed in spot review | insufficient evidence to judge globally | Spot-checked; full cue audit deferred. |

## Proposed next-version changes (not applied)

1. **v0.1.1 evaluator notes:** document heuristic limitations for unsupported-claim and hallucination auto labels.  
2. **v0.1.1 or v0.2:** relax exact instruction-format matching where semantic sections are present.  
3. **v0.2:** add longer max-token cohort or split long-doc answers into structured fields.

## Decision for frozen v0.1

Retain v0.1 unchanged. Report interim scores with evaluator limitations clearly labeled.
