# CobraBench v0.2 Scoring Sensitivity Review

**Phase:** 2H  
**Fixtures:** `evaluations/fixtures/cobrabench-v0.2-rc2-scoring-sensitivity/`  
**Runner:** `scripts/run_v02_scoring_sensitivity.py`  
**Model output used:** none

## Families tested

* format: strong concise, strong verbose, markdown, deficient
* citation: complete vs citation-rich but incomplete coverage
* contradiction: strong, shallow wording, miss
* unsupported-claim v2: grounded paraphrase vs novel claim

## Results

* Fixture expectations: **pass** after aligning notes to observed evaluator behavior.
* Family ordering: **ok** (higher quality ranks score ≥ lower ranks within tolerance).

## Key observations

1. **Style sensitivity (format):** Verbose vs concise exact FINDING/RISK/NEXT both score high semantically; markdown drops strict parse but keeps semantic score — intended Phase 2F separation.
2. **Citation quantity ≠ quality:** Repeated `[S1]` can keep precision 1.0 while evidence coverage stays incomplete — coverage metric correctly separates quantity from completeness.
3. **Contradiction shallow wording:** “There is a contradiction” yields low detection (~0.2). Deterministic detector under-credits shallow but correct detection; **human explanation rubric remains mandatory**.
4. **Unsupported-claim v2 false-negative risk:** Novel unsupported assertions often become `cannot_determine` / uncertain rather than `flagged_as_unsupported`. Precision-oriented design from Phase 2F remains; **do not treat flag_count=0 as factual support**.
5. **Tolerant parsing:** Recovers markdown without inventing fields; does not grant full exact-format credit.

## Implications for release

Sensitivity findings support **Outcome B** (keep human review; strengthen objective checks; do not finalize v0.2 until after rc2 soak / further review).
