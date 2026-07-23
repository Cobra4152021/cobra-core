# CobraBench v0.2 Design

**Status:** Release candidate `cobrabench-v0.2-rc1` frozen — **not final**.  
CobraBench v0.1 remains frozen and unchanged. Official Phase 2D score **0.840** remains valid only under v0.1.

## Goals

- Dual semantic vs exact-format scores
- Versioned unsupported-claim evaluator with measured precision gates
- Citation precision, claim coverage, evidence coverage, contrary-evidence coverage
- Contradiction submetrics (detection through confidence calibration)
- Output-budget / early-stop telemetry fields
- Prompt-template and runtime-profile pins per case
- Uncertainty calibration as a primary category
- Contamination and human-review metadata on every case

## Artifacts

| Artifact | Path |
| --- | --- |
| Requirements | `docs/COBRABENCH_V0_2_REQUIREMENTS.md` |
| Scoring design | `docs/COBRABENCH_V0_2_SCORING_DESIGN.md` |
| Compatibility | `docs/COBRABENCH_V0_1_VS_V0_2_COMPATIBILITY.md` |
| Contamination review | `docs/COBRABENCH_V0_2_CONTAMINATION_REVIEW.md` |
| Schema | `benchmarks/schemas/cobrabench-v0.2-case.schema.json` |
| Typed model | `src/cobra_core/schemas/benchmark_v02.py` |
| Draft examples (non-official) | `benchmarks/drafts/cobrabench-v0.2/` |
| Release candidate | `benchmarks/releases/cobrabench-v0.2-rc1/` |
| Prepared protocol | `evaluations/protocols/qwen3-8b-cobrabench-v0.2-rc1.json` |
| ADR | `docs/decisions/ADR-0006-cobrabench-v0.2-release-candidate.md` |

## Non-goals (Phase 2G)

- Final official v0.2 release
- Migrating or editing v0.1 cases
- Replacing the Phase 2D official score
- Live model evaluation
- Cobra Core designation
