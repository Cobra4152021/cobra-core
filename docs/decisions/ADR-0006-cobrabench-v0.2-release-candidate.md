# ADR-0006 — CobraBench v0.2 Release Candidate

- **Status:** Accepted
- **Date:** 2026-07-22
- **Phase:** 2G

## Context

Phase 2E identified evaluator/prompt/runtime gaps. Phase 2F implemented framework fixes.
Phase 2G constructs a safe CobraBench v0.2 **release candidate** without loading models or scoring any model.

## v0.1 limitations

* Unsupported-claim heuristic noise
* Format semantic/exact conflation
* Contradiction detection vs explanation collapsed
* Limited long-document coverage
* No uncertainty_calibration primary category

## Decision

Freeze **CobraBench v0.2-rc1** with 46 synthetic cases, new weights, evaluator v2 pins, contamination metadata, and single-reviewer approval.

> CobraBench v0.2-rc1 is a release candidate only. It has not been used to evaluate or designate any model as Cobra Core.

## Design

* Case count: 46
* Category architecture: 10 categories (see scoring design)
* Weights total 100%
* Evidence standard: Phase 2F source blocks
* Human review: single-reviewer, 100% approved, 0 unresolved material ambiguities

## Limitations

* Not final
* Not executed on Qwen3-8B or any model
* Deterministic evaluators remain incomplete
* Single-reviewer (not multi-rater)
* Scores not comparable to 0.840

## Next authorized options

1. Independent static review
2. Execute Qwen3-8B against rc1 when hardware is available (separate authorization)
3. Revise rc1 into rc2
4. Freeze final v0.2 after review
5. Resume deferred Phase 2E diagnostics
6. Evaluate another model only with separate authorization
