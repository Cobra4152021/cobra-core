# CobraBench v0.2-rc1 Independent Review Report

**Phase:** 2H  
**Date:** 2026-07-22  
**Reviewer:** `phase2h-static-reviewer-1`  
**Multi-rater:** false  
**Assistance:** hybrid tooling with human judgment  
**Saw original Phase 2G approval notes:** false

## Scope

Static independent review of frozen `cobrabench-v0.2-rc1` (46 cases), plus scoring-sensitivity fixtures, balance/difficulty/template/leakage reviews.  
**No model was loaded or scored.**

## Integrity

* rc1 inventory hash: `87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87` (confirmed)
* rc1 tree hash: `3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10` (confirmed)
* Phase 2D baseline hash unchanged: `84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6`
* Official v0.1 score **0.840** unchanged

## Independence limitations

* Same organization as Phase 2G authoring
* Single reviewer (not multi-rater)
* Tooling assisted scans; judgments remain human-owned
* Original per-case approval notes were not treated as authoritative

## Review coverage

| Status | Count |
| --- | ---: |
| approve unchanged | 0 |
| approve with documentation note | 29 |
| revise before final | 17 |
| remove | 0 |
| unresolved | 0 |

All 46 cases reviewed. No unresolved material ambiguity.

## Defect counts

| Severity | Count (distinct IDs) |
| --- | ---: |
| D0 | 0 |
| D1 | 1 (`D2H-011`) |
| D2 | 7 |
| D3 | 3 (`D2H-001`, `D2H-003`, `D2H-005`) |
| D4 | **0** |

See `evaluations/reviews/cobrabench-v0.2-rc1-independent-review/DEFECTS.json`.

## Category-balance findings

Architecture retained. Refusal (n=3) and uncertainty (n=3) are high-variance. Weights unchanged.

## Difficulty findings

Several hallucination/refusal/citation cases overstated as Level 2; one contradiction case overstated as Level 4. Revised in rc2. Proposed table applied in `RC1_TO_RC2_CHANGES.json`.

## Scoring-sensitivity findings

Style differences mostly separated correctly. Unsupported-claim v2 still under-flags novel claims as `cannot_determine`. Shallow contradiction wording under-scored by deterministic detector. Human review remains required.

## Evaluator-alignment findings

| Issue | Cases | Action |
| --- | --- | --- |
| Mandatory citations on refusal | cb2-037–039 | Removed in rc2 |
| Missing contradictions pin with contrary evidence | cb2-010, cb2-035 | Added in rc2 |
| JSON case wrong template | cb2-041 | exact-format in rc2 |

## Contamination findings

Synthetic-only; no answer-cue phrases in prompts; source-title cue on cb2-027 fixed in rc2.

## Release recommendation

**Outcome B — create rc2.**

Do **not** promote rc1 unchanged (D3 defects present).  
Do **not** create final `cobrabench-v0.2` in this phase.  
Do **not** redesign categories (Outcome C not required).

rc1 remains immutable. rc2 is the corrected release candidate pending further review before finalization.
