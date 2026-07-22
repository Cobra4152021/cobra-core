# Human Review Consistency Check (Phase 2E)

**Type:** Intra-reviewer re-score (not multi-rater agreement).
**Sample size:** 8
**Mean absolute difference:** 0.0363
**Cases with |Δ| ≥ 0.15:** 0

| Case | Category | Original | Second | |Δ| |
| --- | --- | ---: | ---: | ---: |
| cb-015-citation-key-discipline | citation_correctness | 1.00 | 0.95 | 0.05 |
| cb-020-python-parse-log-lines | coding | 1.00 | 0.95 | 0.05 |
| cb-001-evidence-grounded-investigation | evidence_grounding | 0.88 | 0.86 | 0.02 |
| cb-011-missing-source-resistance | hallucination_resistance | 0.90 | 0.88 | 0.02 |
| cb-019-metric-contradiction | contradiction_detection | 0.55 | 0.50 | 0.05 |
| cb-023-long-memo-key-facts | long_document_analysis | 0.75 | 0.72 | 0.03 |
| cb-024-long-policy-exceptions | long_document_analysis | 0.70 | 0.68 | 0.02 |
| cb-027-exact-output-format | instruction_following | 0.70 | 0.65 | 0.05 |

## Notes

- Second pass drafted without displaying original numeric scores.
- Largest disagreements cluster on format and long-document cases — rubric clarification candidates for v0.2.
- Do not claim inter-rater reliability from this check.

## Rubric clarification candidates

