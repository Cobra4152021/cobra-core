# Qwen3-8B CobraBench v0.2-rc2 Evaluation Summary

**Phase 3B outcome:** Readiness framework delivered; **live evaluation blocked** at Gate 3 (smoke).

**Label if later executed:** Experimental release-candidate evaluation — not an official CobraBench v0.2 score.

## Official historical result (unchanged)

| Item | Value |
| --- | --- |
| Benchmark | CobraBench v0.1 |
| Model | Qwen3-8B |
| Official weighted score | **0.840** |
| Baseline inventory hash | `84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6` |

This Phase 3B work did **not** rerun or replace that result.

## Experimental rc2 run

| Item | Value |
| --- | --- |
| Benchmark | CobraBench v0.2-rc2 (non-final) |
| Run ID | *(not created — Gate 3 failed)* |
| Status | `blocked-readiness-failure` |
| Cases attempted | 0 |
| Cases completed | 0 |
| Experimental weighted score | **not reported** |

## Automated preliminary findings

None. Smoke generation did not complete; benchmark execution did not start.

## Pending human findings

Not applicable — no case outputs to review.

## Incomparable score systems

v0.1 and v0.2-rc2 differ in case set, weights, evaluators, and human-review requirements. Direct numerical comparison is prohibited even when an experimental rc2 score later exists.

## Category table

| Category | Case count (rc2) | Completed | Automated score | Human review | Confidence | Warning |
| --- | ---: | ---: | --- | --- | --- | --- |
| *(all rc2 categories)* | 46 total | 0 | n/a | n/a | n/a | live run blocked by smoke crash `0xC0000005` |
| refusal_quality | 3 | 0 | n/a | n/a | low | small-sample |
| uncertainty_calibration | 3 | 0 | n/a | n/a | low | small-sample |

## Smoke failure

Two attempts to load Qwen3-8B (4-bit NF4) crashed the Python process with Windows exit `0xC0000005` at ~75% weight load. See `evaluations/smoke/qwen3-8b-rc2-readiness/`.

## Policy reminders

* `unsupported_claims@2.0.0` remains advisory-only.
* No rc2 result may be labeled official.
* No result may supersede **0.840**.
