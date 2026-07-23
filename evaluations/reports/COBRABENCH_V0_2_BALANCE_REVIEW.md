# CobraBench v0.2 Category Balance Review

**Phase:** 2H  
**Release reviewed:** cobrabench-v0.2-rc1 (architecture retained in rc2)

## Counts and weights

| Category | Cases | Weight |
| --- | ---: | ---: |
| investigation_reasoning | 6 | 18% |
| evidence_grounding | 6 | 14% |
| hallucination_resistance | 5 | 14% |
| citation_correctness | 5 | 14% |
| contradiction_detection | 6 | 12% |
| coding | 4 | 8% |
| long_document_analysis | 4 | 6% |
| instruction_following | 4 | 5% |
| uncertainty_calibration | 3 | 5% |
| refusal_quality | 3 | 4% |

Weights were **not** changed to chase a model score. rc2 keeps identical weights.

## Findings

1. **Investigation + grounding:** Adequately represented (12 cases, 32% weight combined).
2. **Coding influence:** 8% weight / 4 cases — proportionate for Cobra engineering utility; not dominant.
3. **Refusal stability:** Only 3 cases at 4% → high-variance category score (**D2H-013**). Acceptable for rc2 with explicit limitation; do not inflate weight.
4. **Uncertainty vs hallucination:** Distinct intents (calibration vs invention resistance). Some overlap remains; keep both categories.
5. **Long-document diversity:** Four structures present (chrono, multi-source, table+narrative, repeated discrepancy). Adequate for v0.2 scale.
6. **Contradiction types:** Mix of fact, numeric, timeline, identity, apparent, uncertainty-not-contradiction. Not over-concentrated on one type.
7. **Template concentration:** 38/46 `evidence-analysis@2.0.0` (**D2H-010**). Diversity limited; rc2 fixes JSON case template only.
8. **Source-count distribution:** 21 single-source, 17 dual, 8 triple — somewhat skewed to thin evidence; acceptable for hallucination/refusal tasks.
9. **Exact-format density:** 4 instruction cases + coding JSON — not overrepresented.

## Recommendation

Retain architecture; do not redesign categories in Phase 2H. Document refusal/uncertainty small-n limitations.
