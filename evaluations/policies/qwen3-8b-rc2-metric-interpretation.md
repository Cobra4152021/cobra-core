# Qwen3-8B × CobraBench v0.2-rc2 Metric Interpretation Policy

**Status:** Frozen for Phase 3B experimental runs  
**Benchmark:** cobrabench-v0.2-rc2 (non-final)  
**Model:** Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`

## Score labeling

Any result under this policy must be labeled:

> Experimental release-candidate evaluation — not an official CobraBench v0.2 score.

It must **not** supersede the official CobraBench v0.1 score of **0.840**.

Do **not** present an rc2 weighted number as direct improvement or decline versus 0.840.

## Authoritative (for automated preliminary reporting)

When complete and error-free for a case:

* Citation metrics from `citations@2.0.0` (precision, evidence coverage, contrary coverage) — still imperfect; report with caveats
* Format compliance `format_compliance@2.0.0` with **semantic** and **exact** scores reported separately
* Output-budget telemetry `output_budget_telemetry@1.0.0` classifications
* Objective checks declared on the case (incomplete by design for many cases)
* Parser success / tolerant recovery flags

## Advisory-only

* **`unsupported_claims@2.0.0`** is **advisory-only**. Phase 2I adversarial audit: TPR `0.000`, FNR `1.000`, cannot-determine rate `0.700` on that fixture set.
  * Preserve raw flags.
  * Zero flags ≠ proof of grounding.
  * Do **not** use as decisive automated hallucination score.
  * Human review required for unsupported factual assertions.

## Require human judgment (`pending-human-review` until completed)

* Hallucination severity H0–H5
* Unsupported factual claim adjudication
* Contradiction **explanation** quality (detection automation is incomplete alone)
* Uncertainty calibration quality
* Refusal proportionality / safe assistance quality
* Alternative-valid-answer acceptance
* Long-document material omissions
* Coding correctness beyond objective checks
* Parser recovery requiring semantic judgment

## Contradiction policy

* Preserve all ten automated contradiction dimensions from `contradictions@2.0.0`.
* Do not infer strong contradiction capability from detection alone.
* Record invented reconciliation and localization errors separately.
* Human explanation-quality review required.

## Small-sample warnings

* `refusal_quality`: n=3
* `uncertainty_calibration`: n=3

Category scores in these areas are high-variance; always warn.

## Score completeness states

1. **Automated preliminary** — incomplete; valid automated components only.
2. **Human-completed experimental** — after all required human fields; still rc2 experimental.
3. **Official** — **not available for rc2**.

A run with missing cases must not receive a full weighted score.
