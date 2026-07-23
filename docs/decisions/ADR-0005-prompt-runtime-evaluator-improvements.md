# ADR-0005 — Prompt, Runtime, and Evaluator Improvements

- **Status:** Accepted
- **Date:** 2026-07-22
- **Phase:** 2F

## Context

Phase 2E showed that several “model weaknesses” were evaluator, prompt, or telemetry gaps.
Live diagnostic generations remain deferred. Phase 2F implements framework improvements without loading models.

## Phase 2E evidence

- W01 unsupported-claim heuristic ≈0% precision / ≈100% FPR on a 50-flag audit sample
- W07 keyword/parser brittleness
- W02 citation-key habits; W04 semantic-correct / syntactic-fail format cases
- W05 output budgeting; W06 early long-document completion (not simple 512 truncation)
- W03 contradiction explanation depth still unconfirmed without live controls

## Evaluator-v1 limitations

v1 unsupported-claim counting treated many uncited sentences, headings, and paraphrases as unsupported.
Official CobraBench v0.1 continues to reference v1 for historical validity.

## Changes implemented

- Explicit evaluator registry and immutable version metadata
- Unsupported-claim evaluator v2 (classify-then-support)
- Semantic vs exact-format scoring; strict and tolerant parsers
- Citation metrics v2 (precision, claim/evidence/contrary coverage)
- Contradiction submetrics
- Output-budget / early-stop telemetry
- Versioned prompt templates and runtime policy profiles
- Prospective CobraBench v0.2 schema + non-official draft cases
- Offline reevaluation of historical Phase 2D outputs into new directories

## Compatibility impact

v1 and v2 scores are **not** directly comparable.
Official baseline **0.840** is unchanged.
Offline v2 results are labeled diagnostic only.

## Risks

- Over-trusting deterministic support matching
- Treating v2 improvements as model progress
- Accidentally applying v2 templates to frozen v0.1 runs

## Unknowns

- Live thinking / prompt / delimiter / stability effects (still deferred)
- Quantization impact (still unknown)

## Decision

> Phase 2F improves prompts, runtime policies, parsers, and evaluators. It does not change the official CobraBench v0.1 baseline, authorize training, or designate any model as Cobra Core.

## Next authorized options

1. Re-attempt Phase 2E live diagnostics when hardware is free (new run ID).
2. Prepare and review an official CobraBench v0.2 release (separate authorization).
3. Run offline evaluator-v2 rescoring on additional historical outputs.
4. Evaluate another practical model only with separate authorization.
5. Begin dataset design only if future controlled diagnostics establish Class 4 weaknesses.
