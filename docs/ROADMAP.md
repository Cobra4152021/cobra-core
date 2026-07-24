# Cobra Model Lab Roadmap

**Last updated:** 2026-07-23 (Phase 3G roadmap draft)

## Completed

| Phase | Summary |
| --- | --- |
| Phase 1 | Cobra Model Lab foundation |
| Phase 2A | Qwen candidate intake and baseline selection |
| Phase 2B | Qwen3-8B acquisition and local inference validation |
| Phase 2C | Qwen3-32B local-runtime feasibility stop |
| Phase 2D | Qwen3-8B CobraBench **v0.1** official interim baseline (**0.840**) |
| Phase 2E | Static weakness analysis; live diagnostics deferred |
| Phase 2F | Evaluator, parser, prompt, runtime, telemetry framework |
| Phase 2G | CobraBench v0.2-rc1 |
| Phase 2H | Independent review → v0.2-rc2 |
| Phase 2I | Second review → Outcome D (rc2 remains non-final) |
| Phase 3A | Reviewer kit + Milestone M1 governance freeze |
| Phase 3B–3E | Windows/WSL runtime isolation path; WSL unavailable (Outcome E) |
| Phase 3F | Cloud Linux runtime qualification on RunPod — **Outcome A**; tag `phase-3f-qualified` |

## Active / upcoming

| Phase | Intent | Gate |
| --- | --- | --- |
| **Phase 3G** | Cloud runtime production-readiness optimization (equivalence-preserving); **no benchmark execution** | **P1 implemented** (ops/pins/docs). P2+ require separate approval — see `docs/phases/PHASE_3G_STATUS.md` |
| Later | Controlled CobraBench v0.2-rc2 on locked cloud runtime | Separate authorization; remains `prepared-not-run` until then |

## Future (not authorized by M1)

* Candidate comparison campaigns
* **Cobra Core** designation (explicit future decision only)
* Training / LoRA / QLoRA (only if justified by evidence and separately authorized)
* Final CobraBench v0.2 freeze (requires genuine second-reviewer Outcome A or justified rc3 path)

## Rules

* Official scores never silently change.
* Release candidates do not supersede official benchmarks.
* Model evaluation is separate from benchmark engineering.
* No training by default.
