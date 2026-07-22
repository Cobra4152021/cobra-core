# Phase 2E Status — Qwen3-8B Weakness Analysis

**Milestone status:** Partial closure — static analysis complete; live diagnostic cohorts deferred.  
**Date:** 2026-07-22  
**Baseline run:** `20260722T200000Z-8bba5e01` (locked)  
**Planned diagnostic run:** `20260722T220000Z-2ediag01` (blocked before generation)

This phase is **not** fully complete. Do not treat deferred cohort measurements as failed model-quality tests.

## Completed

- Static analysis of **28/28** baseline cases
- Weakness taxonomy (`docs/QWEN3_8B_WEAKNESS_TAXONOMY.md`)
- Case-level cause classification (`evaluations/analysis/qwen3-8b-v0.1-case-analysis.json`)
- Unsupported-claim heuristic audit
- Exact-format compliance audit
- Long-document static analysis
- Contradiction static analysis
- Evidence-grounding static analysis
- Human rescoring consistency check (intra-reviewer)
- Weakness matrix
- Quantization limitations documentation
- CobraBench v0.2 proposal (prospective only)
- ADR-0004 decision (Outcome A + B)
- Controlled diagnostic cohort definitions
- Diagnostic dry-run (25 jobs planned)
- Baseline lock for Phase 2D interim result

## Deferred

- Thinking-enabled versus disabled measurements
- Output-cap controlled measurements
- Prompt-format controlled measurements
- Evidence-delimiter controlled measurements
- Sampling-stability measurements
- Measured cohort deltas
- Live diagnostic comparison reports derived from new generations

## Reason deferred

Local GPU/RAM contention caused Qwen3-8B model loading to fail with Windows access violation:

`0xC0000005`

At the blocked attempt, roughly **6 GB** of GPU VRAM was already in use by other processes and free system RAM was low (~5 GB). No diagnostic generations completed.

See:

- `evaluations/reports/PHASE2E_DIAGNOSTIC_RUN_STATUS.md`
- `evaluations/analysis/phase2e-blocked-diagnostic-run.json`
- `docs/PHASE_2E_DIAGNOSTICS_RUNBOOK.md`

## Explicit non-claims

- Phase 2E does **not** authorize LoRA, QLoRA, full fine-tuning, dataset collection, new model acquisition, or Cobra Core designation.
- No weakness is Class 4 adaptation-eligible until controlled diagnostics complete.
- Diagnostic results must not be mixed into the official CobraBench v0.1 score of **0.840**.
