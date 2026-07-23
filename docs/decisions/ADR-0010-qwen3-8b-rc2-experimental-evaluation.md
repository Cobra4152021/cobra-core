# ADR-0010 — Qwen3-8B × CobraBench v0.2-rc2 experimental evaluation (Phase 3B)

## Status

Accepted for Phase 3B readiness outcome: **live evaluation blocked**.

## Context

Phase 3A froze reviewer-kit governance and confirmed CobraBench v0.2-rc2 as a non-final release candidate. Phase 3B authorized preparation and, only if all readiness gates pass, one controlled Qwen3-8B evaluation against the frozen rc2 bundle.

Official CobraBench v0.1 Qwen3-8B weighted score remains **0.840**.

## Why rc2 was evaluated before final v0.2

rc2 incorporates Phase 2H Outcome B case fixes and remains the best available candidate bundle for experimental measurement, but Phase 2I Outcome D blocked finalization (no genuine second-reviewer separation; unsupported-claim v2 false-negative risk; small refusal/uncertainty samples). An experimental run was therefore the maximum authorized live step — not final scoring.

## Governance limitations

* Genuine second independent human reviewer was not achieved for rc2.
* Unsupported-claim evaluator `2.0.0` is advisory-only (Phase 2I adversarial audit: TPR 0.000, FNR 1.000, cannot_determine 0.700).
* Refusal and uncertainty categories have n=3.
* Final CobraBench v0.2 has not been released.

## Exact model configuration (intended)

| Field | Value |
| --- | --- |
| Model | Qwen3-8B |
| Upstream | https://huggingface.co/Qwen/Qwen3-8B |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Quantization | bitsandbytes 4-bit NF4, double quant, float16 compute |
| trust_remote_code | false |
| device_map | auto |
| Seed | 123 |
| Temperature | 0.0 |
| Thinking | disabled |

## Execution protocol

Prepared protocol (immutable status `prepared-not-run`):

`evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc2.json`

Execution was planned via a versioned copy under `evaluations/runs/<RUN_ID>/protocol.json` using `scripts/run_cobrabench_v02_rc2.py` and `cobra_core.evaluation.rc2_run`.

## Unsupported-claim advisory status

`unsupported_claims@2.0.0` outputs would have been preserved as advisory-only and never used as a decisive automated hallucination score. Policy: `evaluations/policies/qwen3-8b-rc2-metric-interpretation.md`.

## Human-review requirements

Human-required fields (unsupported claims / H0–H5, contradiction explanation quality, uncertainty, refusal, etc.) must remain `pending-human-review` until actually reviewed. No fabricated ratings.

## Score-comparison restrictions

No rc2 result may be labeled official. No direct numerical comparison against **0.840** is permitted.

## Run outcome

**Readiness failure at Gate 3 (smoke).**

* Gate 1 (static integrity): passed (quality suite green; frozen hashes matched).
* Gate 2 (preflight / model inventory): passed.
* Gate 3 (smoke): **failed** — two process crashes `0xC0000005` during 4-bit weight load (~75% of 399 modules). One environmental retry was authorized and exhausted.
* Gates 4–10: metric policy and readiness framework artifacts created; controlled 46-case execution **not started**.
* No run workspace case outputs exist because the smoke gate failed.

Artifacts:

* `evaluations/preflight/qwen3-8b-v0.2-rc2-preflight.json`
* `evaluations/model-inventory/qwen3-8b-local-inventory.json`
* `evaluations/smoke/qwen3-8b-rc2-readiness/`
* `evaluations/policies/qwen3-8b-rc2-metric-interpretation.md`
* `evaluations/reports/QWEN3_8B_COBRABENCH_V0_2_RC2_SUMMARY.md`
* Runner: `src/cobra_core/evaluation/rc2_run.py`, `scripts/run_cobrabench_v02_rc2.py`

## Limitations

* Host exhibits recurring ACCESS_VIOLATION during Qwen3-8B 4-bit load (also seen in Phase 2E diagnostics).
* Desktop GPU contention (~2.3 GiB reserved by UI processes) may contribute but was not proven causal.
* Exact prior successful v0.1 load conditions were not reproduced in this session.

## Next authorized options

Require separate authorization for any of:

1. Host remediation / GPU process quarantine, then a new smoke attempt.
2. Controlled rc2 execution after smoke pass.
3. Alternative runtime path investigation (without silently changing model revision).
4. External independent human review to advance beyond Outcome D (outside this ADR’s execution scope).

## Decision statement

> This Phase 3B result is experimental and does not supersede the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, or designate Qwen3-8B as Cobra Core.

Additionally: Phase 3B did **not** produce an experimental rc2 score because Gate 3 failed.
