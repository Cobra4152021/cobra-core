# Unsupported-Claim v2 False-Negative Audit

**Phase:** 2I  
**Evaluator:** unsupported_claims **2.0.0** (not modified)  
**Fixtures:** `evaluations/fixtures/unsupported-claims-v2-false-negative/`

## Metrics (adversarial n=10)

| Metric | Value |
| --- | ---: |
| True-positive rate | 0.000 |
| False-negative rate | 1.000 |
| False-positive rate (controls) | 0.000 |
| cannot_determine rate (adversarial) | 0.700 |

## Interpretation

Novel unsupported assertions frequently land in `cannot_determine` / uncertain rather than `flagged_as_unsupported`.
This matches Phase 2H findings and is an intentional precision tradeoff from Phase 2F.

**Do not change evaluator 2.0.0 in place.** A prospective `2.1.0` may be proposed later and would require rc3 or delayed finalization if pinned into the benchmark.

## Release impact

Document as known limitation. Blocks silent claims of automated hallucination completeness.
