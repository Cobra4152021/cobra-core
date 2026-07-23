# Qwen3-8B Offline Reevaluation v2

> Offline evaluator-v2 diagnostic results

**Source run:** `20260722T200000Z-8bba5e01`  
**Generated:** 2026-07-23T00:08:09.429590+00:00  
**Official baseline score:** unchanged at **0.840**

## Scope

- Cases reevaluated offline: **15**
- No model load / no live generation
- Outputs written outside the immutable Phase 2D directory

## Unsupported-claim v1 vs v2

| Case | v1 flags | v2 flags | v2 uncertain |
| --- | ---: | ---: | ---: |
| `cb-001-evidence-grounded-investigation` | 20 | 0 | 5 |
| `cb-002-contradictory-witness-statements` | 19 | 0 | 16 |
| `cb-003-citation-unsupported-claim-detection` | 7 | 0 | 3 |
| `cb-008-log-vs-witness-grounding` | 8 | 0 | 5 |
| `cb-009-inventory-count-grounding` | 3 | 0 | 2 |
| `cb-010-email-thread-grounding` | 1 | 0 | 1 |
| `cb-015-citation-key-discipline` | 1 | 0 | 0 |
| `cb-016-misattributed-quote-detection` | 3 | 0 | 0 |
| `cb-017-citation-for-inference` | 5 | 1 | 2 |
| `cb-018-schedule-contradiction` | 6 | 0 | 2 |
| `cb-019-metric-contradiction` | 2 | 0 | 2 |
| `cb-023-long-memo-key-facts` | 10 | 0 | 5 |
| `cb-024-long-policy-exceptions` | 9 | 0 | 5 |
| `cb-027-exact-output-format` | 3 | 0 | 2 |
| `cb-028-json-only-response` | 0 | 0 | 0 |

## Format compliance (diagnostic)

| Case | semantic | exact | strict parse | tolerant parse |
| --- | ---: | ---: | --- | --- |
| `cb-027-exact-output-format` | 1.00 | 0.40 | False | True |
| `cb-028-json-only-response` | 0.00 | 0.00 | False | False |

## Early-stop / budget telemetry

| Case | tokens | % budget | class |
| --- | ---: | ---: | --- |
| `cb-001-evidence-grounded-investigation` | 512 | 100.0 | `likely_budget_exhaustion` |
| `cb-023-long-memo-key-facts` | 127 | 24.8 | `stopped_before_required_sections` |
| `cb-024-long-policy-exceptions` | 128 | 25.0 | `stopped_before_required_sections` |

## Interpretation

- v2 reduces noisy unsupported flags versus v1 on the same texts.
- Format dual scores show semantic content can pass while exact syntax fails.
- Long-document baseline outputs with low budget use classify as natural/early completion, not budget exhaustion.
- Cases needing future live diagnostics remain those involving thinking mode, prompt variants, and delimiter experiments (still deferred from Phase 2E).

## Compatibility

See `docs/EVALUATOR_VERSIONING_AND_SCORE_COMPATIBILITY.md`.
Do not mix these diagnostics into the official 0.840 baseline.

