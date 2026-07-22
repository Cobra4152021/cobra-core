# Phase 2E Diagnostic Run Status

**Milestone:** Phase 2E **partial closure** — static analysis complete; live cohorts deferred.  
See also `docs/PHASE_2E_STATUS.md` and `evaluations/analysis/phase2e-blocked-diagnostic-run.json`.

| Field | Value |
| --- | --- |
| Planned run ID | `20260722T220000Z-2ediag01` |
| Planning completed | Yes |
| Planned jobs | **25** |
| Dry-run | **Passed** |
| Generations completed | **0** |
| Official CobraBench? | **No** |
| Baseline lock | `evaluations/baselines/qwen3-8b-cobrabench-v0.1.json` (immutable) |
| Result | **Blocked before generation** (not a model-quality test failure) |
| Crash code | `0xC0000005` (ACCESS_VIOLATION) during weight load (~20%) |
| Hardware when blocked | ~6 GB VRAM already in use; ~5.1 GB free system RAM |
| Partial output | Plan JSON only; **no** response texts |
| Resumable under same ID? | **No** — use a **new** run ID for live execution |
| New run ID required | **Yes** |

## Completed vs deferred

**Completed:** cohort definitions, 25-job plan, dry-run validation, blocked-run metadata.  
**Deferred:** thinking / output-cap / prompt / delimiter / stability measurements and measured comparison reports.

## Baseline protection note

A Phase 2E-only `human-consistency-check.json` was briefly written into the locked Phase 2D run directory and was relocated to `evaluations/analysis/`. Inventory hash restored to `84b0972f…`. Analysis scripts must not write into locked runs.

## Follow-up

Use `docs/PHASE_2E_DIAGNOSTICS_RUNBOOK.md`. Closing apps does not guarantee load success.
