# Phase 4 — Capability Validation Plan

## 1. Mission

Validate real-world usefulness of the Phase 3F–qualified runtime under representative user workloads, while preserving runtime equivalence and evaluation integrity.

## 2. Baseline & invariants

| Item | Value |
| --- | --- |
| Qualified runtime tag | `phase-3f-qualified` |
| Documentation baseline | `db43ff25aee6c9ea60ddd97fa5ac9824678fda51` |
| Model | Qwen3-8B @ `b968826d9c46dd6066d109eabc6255188de91218` |
| Inventory hash | `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f` |
| Quant / device | bnb 4-bit NF4 double, float16, `device_map={"": 0}` |
| Official score | **0.840** (do not alter reporting) |
| CobraBench | remains `prepared-not-run` |

## 3. In scope

| Domain | Focus |
| --- | --- |
| Code generation | Python, TypeScript, SQL, Shell, Cloudflare Workers, debugging, refactoring |
| Research | Long-doc reasoning, evidence extraction, citation consistency, structured summaries |
| Investigator | Timeline, evidence org, contradiction detection, confidence reporting |
| Business | Planning, tech docs, architecture reviews, SOP generation |
| Reliability | Repeatability, determinism checks, malformed inputs, large context |

## 4. Out of scope (Phase 4 framework & future execution)

- Retraining / LoRA / fine-tuning
- CobraBench execution or case mutation
- Deployment / public endpoints
- Model replacement or quant changes
- Prompt-engineering campaigns aimed at raising **0.840**
- Designating “Cobra Core” as a product model solely from this suite

## 5. Method (when execution is later authorized)

1. Recreate locked cloud Linux env (`phase3g_verify_env.py` must pass).
2. Run tasks from `TASK_CATALOG.md` in the recommended order.
3. Score with `SCORING_RUBRIC.md` (human primary; optional rule checks).
4. Apply `PASS_FAIL_CRITERIA.md` at domain and suite level.
5. Store evidence under a new diagnostics directory (future); never overwrite Phase 3F freeze.
6. Report usefulness estimates and failure modes; do not convert results into official scores.

## 6. Roles

| Role | Responsibility |
| --- | --- |
| Operator | Env bring-up, inference, export, cleanup |
| Scorer | Blind-ish review against rubric (see human-review norms in EVALUATION_POLICY) |
| Auditor | Confirm no pin drift, no CobraBench run, no secret leakage |

## 7. Prompt policy

- Use **workload prompts** defined in the task catalog (synthetic / public-safe fixtures).
- Do not paste private investigation cases or proprietary business data.
- Do not iteratively rewrite prompts mid-suite to improve scores; file defects instead.
- Prefer the evidence answer convention from `docs/COBRA_EVIDENCE_PROMPT_STANDARD.md` for research/investigator tasks.

## 8. Runtime policy

- Fresh process per task batch when measuring reliability/determinism.
- Record temperature/seed/max tokens if the runner exposes them; default to the qualified runtime profile used in Phase 3F smoke unless a task specifies otherwise.
- Peak VRAM and load times are telemetry only — not usefulness scores.

## 9. Evidence package (future execution)

Suggested layout (create only when executing):

```text
evaluations/diagnostics/phase-4-capability-validation/
  RUN.md
  environment.json
  tasks/<task_id>/{prompt.txt,output.txt,score.json}
  DOMAIN_SUMMARY.json
  SUITE_SUMMARY.json
  SHA256SUMS
```

## 10. Relationship to CobraBench

| | CobraBench | Phase 4 Capability Validation |
| --- | --- | --- |
| Purpose | Formal scored benchmark | User-workload usefulness |
| Status now | prepared-not-run / 0.840 official v0.1 | Framework only |
| May replace official score? | Only via versioned official run | **Never** |
| Prompt gaming for 0.840 | Forbidden | Forbidden |

## 11. Success definition (suite)

The suite succeeds as a **framework** when this directory is complete and reviewable.  
The suite succeeds as an **execution** (later) when pass/fail criteria are applied and a `SUITE_SUMMARY.json` exists with integrity fields intact.
