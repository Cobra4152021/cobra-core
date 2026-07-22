# ADR-0004 — Qwen3-8B Weakness Analysis Decision

- **Status:** Accepted (Phase 2E partial closure)
- **Date:** 2026-07-22
- **Phase:** 2E — Weakness analysis and controlled diagnostics

## Context

Phase 2D produced an interim CobraBench v0.1 score of **0.840** for Qwen3-8B (4-bit, thinking disabled). Phase 2E completed static analysis of all 28 cases, audited noisy automation, locked the baseline, and defined controlled diagnostic cohorts. Live diagnostic generations were **blocked before generation** by a Windows access violation (`0xC0000005`) under GPU/RAM contention. Phase 2E is therefore a **partial milestone**: static analysis complete; live cohorts deferred.

## Evidence supporting the decision

- **14** cases showed no primary weakness class.
- **11** were classified as suspected model weaknesses (**M**).
- **2** were primarily scoring/parser issues (**S**).
- **1** was primarily prompt-related (**P**).
- Unsupported-claim heuristic precision was approximately **0%** on the 50-flag audit sample (false-positive rate approximately **100%**).
- Exact-format failure was **semantically correct** but **syntactically noncompliant**.
- Contradiction **detection** and contradiction **explanation** are separable capabilities.
- Long-document cases completed at approximately **127–128** output tokens and were **not** simply truncated by the 512-token cap.
- No controlled live cohort has yet confirmed thinking-mode, prompt, delimiter, stability, or token-cap effects.

## Decision

**Outcome A + Outcome B**

- **A — Optimize prompts and runtime controls first** (format clarification, evidence delimiters, token budgeting / higher caps for verbose investigation, thinking-mode cohort when the host can load safely).
- **B — Improve the evaluation framework and prepare CobraBench v0.2** (version noisy heuristics; dual semantic/exact format scores; split contradiction submetrics). Do **not** begin training.

**Not selected now**

- **C** Evaluate another model — premature until deferred diagnostics finish.
- **D** Authorize dataset design / adaptation — **not authorized**.
- **E** Stronger hardware — optional enabler later; not required to close static Phase 2E.

> No weakness is currently eligible for Class 4 model adaptation because controlled diagnostics have not completed.

> Phase 2E does not authorize LoRA, QLoRA, full fine-tuning, dataset collection, new model acquisition, or designation of Qwen3-8B as Cobra Core.

## Next authorized options

1. Follow `docs/PHASE_2E_DIAGNOSTICS_RUNBOOK.md` and run diagnostics with a **new** run ID when GPU/RAM conditions allow a safe load.
2. Implement evaluator-v0.1.1 / heuristic versioning documentation (no silent v0.1 rescore; no v0.1 case edits).
3. Draft CobraBench v0.2 cases only after separate authorization.
4. Only later: consider Class 4 adaptation targets if W03/W06 persist after Class 1–3 controls.

## Risks

- Overfitting narrative to static analysis without diagnostic confirmation.
- Treating heuristic flags as model hallucinations.
- Inflating the official 0.840 score with diagnostic prompts.

## Unknowns (require live diagnostics)

- Thinking-mode effect sizes.
- Whether higher output caps change early long-document completion.
- Prompt-format and evidence-delimiter effect sizes.
- Sampling stability under deterministic settings.
- 4-bit versus BF16/8-bit quality delta.
