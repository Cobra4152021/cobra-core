# ADR-0007 — CobraBench v0.2 Independent Review

- **Status:** Accepted
- **Date:** 2026-07-22
- **Phase:** 2H

## Context

Phase 2G froze CobraBench v0.2-rc1 (46 synthetic cases) with single-reviewer authoring/approval. Phase 2H performs a separate independent static review and selects a release outcome.

## rc1 state

* Inventory hash: `87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87`
* Tree hash: `3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10`
* Non-final; no model evaluated

## Review independence

* Reviewer: `phase2h-static-reviewer-1`
* Original approval notes hidden / not authoritative
* Hybrid tooling + human judgment
* **Not multi-rater**
* Same-organization limitation documented

## Methodology

Per-case clarity/answerability/fairness/evidence/scoring/relevance/budget review; reference-behavior challenge; balance; difficulty; scoring sensitivity fixtures; evaluator matrix; template/profile review; leakage recheck; D0–D4 classification.

## Findings summary

* D4: 0
* D3: 3 (vacuous objective checks; UTC source-title cue; refusal citation unfairness)
* D2/D1: title cues, evaluator pins, difficulty mislabels, template mismatch, small-n refusal, date clustering

## Release outcome

**Outcome B — create rc2**

* rc1 remains immutable
* `benchmarks/releases/cobrabench-v0.2-rc2/` created with targeted corrections
* Final `cobrabench-v0.2/` **not** created
* Protocols remain `prepared-not-run`

> Phase 2H does not evaluate Qwen3-8B, change the official CobraBench v0.1 score, authorize training, or designate any model as Cobra Core.

## Limitations

* Single independent reviewer
* Deterministic evaluators still incomplete proxies
* rc2 still a release candidate
* Scores not comparable across v0.1 / rc1 / rc2 without qualification

## Next authorized options

1. Seek a second human reviewer for rc2
2. Run Qwen3-8B on rc2 after another review (separate authorization)
3. Revise rc2 → rc3 if new D3/D4 found
4. Freeze final v0.2 only after Outcome A criteria are met
5. Resume Phase 2E controlled diagnostics (separate authorization)
6. Evaluate another model only with separate authorization
