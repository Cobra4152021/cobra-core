# CobraBench v0.2 Design (Draft)

**Status:** Design / draft schema only — **not released**.  
CobraBench v0.1 remains frozen and unchanged.

## Goals

- Dual semantic vs exact-format scores
- Versioned unsupported-claim evaluator with measured precision gates
- Citation precision, claim coverage, evidence coverage, contrary-evidence coverage
- Contradiction submetrics (detection ≠ explanation)
- Output-budget / early-stop telemetry fields
- Prompt-template and runtime-profile pins per case
- Immutable baseline write protection and diagnostic/official separation

## Artifacts

- Schema: `benchmarks/schemas/cobrabench-v0.2-case.schema.json`
- Typed model: `src/cobra_core/schemas/benchmark_v02.py`
- Draft examples: `benchmarks/drafts/cobrabench-v0.2/` (non-official, not scored, not frozen)

## Non-goals for this phase

- Official v0.2 release
- Migrating or editing v0.1 cases in place
- Replacing the Phase 2D official score
