# Cobra Model Lab Roadmap

**Last updated:** 2026-07-23 (Phase 3A / Milestone M1)

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

## Upcoming

| Phase | Intent | Gate |
| --- | --- | --- |
| **Phase 3B** | Official Qwen3-8B evaluation reporting hygiene against **v0.1** (no score rewrite) | Separate authorization; do not alter 0.840 |
| **Phase 3C** | Qwen3-8B evaluation against **rc2** only after stronger review / Outcome A path | Separate authorization; prepared-not-run until executed |
| **Phase 3D** | Controlled Phase 2E-style diagnostics under resource guards | Separate authorization; new run IDs only |

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
