# CobraBench v0.1 versus v0.2 Compatibility

## Summary

Historical **0.840** remains valid only under CobraBench **v0.1**.
v0.2-rc1 / v0.2-rc2 scores must **not** be presented as direct improvement or decline versus 0.840 without qualification.

**Final CobraBench v0.2 has not been released** (Phase 2I Outcome D).

## Phase 2I second-review findings

* Outcome **D**: keep rc2 non-final — genuine second-reviewer separation was not achieved.
* No rc3 created.
* No final `cobrabench-v0.2/` created.
* Category definitions and weights unchanged.
* Evaluator versions unchanged (unsupported_claims/citations/contradictions/format **2.0.0**; telemetry **1.0.0**).
* Unsupported-claim v2 adversarial audit: high false-negative / cannot_determine rates; do not treat flag_count=0 as factual support.
* Refusal and uncertainty remain small-sample categories (n=3); variance warning required if ever finalized.
* Partial residual: some rc2 objective checks remain thin outside refusal/citation/contradiction/JSON categories.

## Why scores are not interchangeable

| Dimension | v0.1 | v0.2-rc1 | v0.2-rc2 | final v0.2 |
| --- | --- | --- | --- | --- |
| Status | frozen official baseline | immutable RC | immutable RC | **not released** |
| Categories | 9 | 10 | 10 | — |
| Weights | v0.1 table | v0.2 table | same as rc1 | — |
| Unsupported-claim | v1 | v2 | v2 (known FN risk) | — |

Actual v0.2 weights (frozen): investigation 18%, grounding 14%, hallucination 14%, citation 14%, contradiction 12%, coding 8%, long-document 6%, instruction 5%, uncertainty 5%, refusal 4%.

## Score-comparison restrictions

* Do not convert among v0.1 / rc1 / rc2.
* Do not invent a conversion formula.
* Always display release ID and evaluator versions.
* Official Phase 2D baseline artifacts must not be overwritten.

## Official score

The official Qwen3-8B score remains:

**0.840 under CobraBench v0.1**
