# ADR-0008 — CobraBench v0.2 Second Review

- **Status:** Accepted
- **Date:** 2026-07-23
- **Phase:** 2I

## Context

Phase 2H produced immutable rc2 after Outcome B. Phase 2I requires a **second** independent review before final v0.2 promotion.

## rc2 state

* Inventory hash: `08f04c10267b3f772d7783a332d816947486812f7a983dff070bdad442708cc6`
* Tree hash: `1d438415c22827155f57817ace9274aee6c9e47048e4f6443a249ba7a5f2314f`
* Case count: 46
* Protocol: `prepared-not-run`

## Reviewer independence

* Reviewer: `phase2i-second-static-reviewer-1`
* Participated in Phase 2G authoring workflow: **yes**
* Participated in Phase 2H review: **yes**
* Genuine separation achieved: **false**
* Blind answerability performed before rubric consultation: **yes**
* Multi-rater: **false**

Preferred independence conditions were **not** met.

## Blind review method

All 46 cases reviewed using only prompt, evidence, and constraints before reading expected behaviors.

## Rubric comparison

* agreement: 31
* acceptable_alternative: 15
* no unsupported expected behaviors found that invalidate answerability

## Revision verification

* 17 Phase 2H `revise_before_final` cases verified
* 10 fully resolved
* 7 partially resolved (objective-check enrichment still thin for some categories)
* 0 failed / reverted

## Unsupported-claim audit

Evaluator 2.0.0 left unchanged. Adversarial fixture set shows high false-negative / cannot_determine rates for novel unsupported claims. Prospective `2.1.0` may be needed later and would require a new release candidate if pinned.

## Contradiction audit

Ordering OK for full vs miss / preserve vs miss. Shallow wording still under-scored; human explanation scoring remains required.

## Small-sample review

Refusal and uncertainty remain n=3 each. Weights unchanged. Small-sample warnings required if ever finalized.

## Diversity / robustness

No contamination. Template regularity and date clustering are diversity limitations. Format/contradiction ordering directionally correct.

## Defects by severity

* D0: case-level none recorded in register (many approve_unchanged)
* D1: documentation / small-sample notes
* D2: UC FN risk, contradiction shallow-wording, partial objective enrichment, diversity
* D3: 0
* D4: 1 (process — lack of genuine second-reviewer separation)

## Release decision

**Outcome D — Keep rc2 non-final**

Final `cobrabench-v0.2/` not created. rc3 not created. rc1 and rc2 remain immutable.

> Phase 2I does not evaluate Qwen3-8B, alter the official 0.840 CobraBench v0.1 score, authorize training, or designate any model as Cobra Core.

## Limitations

* No separate human second reviewer
* Deterministic evaluators remain incomplete proxies
* UC v2 adversarial TPR measured at 0.0 on this fixture set (cannot_determine-dominant)
* Refusal/uncertainty small-n variance

## Next authorized actions

1. Obtain a separate human reviewer who did not author cases or perform Phase 2H
2. Re-run Phase 2I gates with that reviewer toward Outcome A or B
3. Optionally design unsupported_claims 2.1.0 + rc3 under separate authorization
4. Execute Qwen3-8B on a final v0.2 only after Outcome A
5. Resume Phase 2E diagnostics only with separate authorization
