# Capability Validation Package — Phase 4

**Status:** Framework only — **not executed**  
**Baseline runtime:** `phase-3f-qualified`  
**Docs baseline:** `db43ff25aee6c9ea60ddd97fa5ac9824678fda51`  
**Official CobraBench v0.1 score:** **0.840** (unchanged)  
**CobraBench v0.2-rc2:** `prepared-not-run` (unchanged)

## Purpose

Evaluate whether the smoke-qualified Qwen3-8B cloud Linux runtime is **genuinely useful** for representative user workloads (code, research, investigator, business, reliability) — without retraining, benchmark gaming, deployment, or model replacement.

## Documents

| Document | Contents |
| --- | --- |
| [VALIDATION_PLAN.md](./VALIDATION_PLAN.md) | Scope, constraints, method, roles, evidence rules |
| [TASK_CATALOG.md](./TASK_CATALOG.md) | Representative tasks per capability |
| [SCORING_RUBRIC.md](./SCORING_RUBRIC.md) | How to score each response |
| [PASS_FAIL_CRITERIA.md](./PASS_FAIL_CRITERIA.md) | Suite-level and domain-level gates |
| [FUTURE_AUTOMATION_PLAN.md](./FUTURE_AUTOMATION_PLAN.md) | How to automate later (not now) |
| [CAPABILITY_MATRIX.md](./CAPABILITY_MATRIX.md) | Compact matrix of capabilities × usefulness |
| [RECOMMENDED_EXECUTION_ORDER.md](./RECOMMENDED_EXECUTION_ORDER.md) | Wave order for a future authorized run |

Product identity & gates: `docs/product/` (Phase 4.1).  
Pilot (Phase 4.2): `docs/capability-validation/pilot/` — framework practicality validated; full 46-task run still requires separate authorization.

## Hard rules

1. Do **not** execute tasks until a separate authorization says so.
2. Do **not** run CobraBench as part of this suite.
3. Do **not** change prompts to chase the **0.840** score.
4. Preserve qualified pins (model revision, quant, device_map, dependency locks).
5. Label all Phase 4 results as **workload validation**, never as official benchmark scores.
