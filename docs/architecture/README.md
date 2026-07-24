# Architecture package (Phase 3G.5)

Documentation-only package describing how Cobra Core is structured and how cloud qualification is operated. **Does not change runtime behavior.**

| Document | Purpose |
| --- | --- |
| [OVERALL.md](./OVERALL.md) | End-to-end Cobra Core architecture |
| [RUNTIME_QUALIFICATION_WORKFLOW.md](./RUNTIME_QUALIFICATION_WORKFLOW.md) | Phase 3F-style smoke qualification gates |
| [CLOUD_EXECUTION_WORKFLOW.md](./CLOUD_EXECUTION_WORKFLOW.md) | Provision → transfer → run → export |
| [EVIDENCE_GENERATION_WORKFLOW.md](./EVIDENCE_GENERATION_WORKFLOW.md) | How qualification evidence is produced and frozen |
| [CLEANUP_WORKFLOW.md](./CLEANUP_WORKFLOW.md) | Terminate and verify zero remaining spend |
| [DEPENDENCY_RELATIONSHIPS.md](./DEPENDENCY_RELATIONSHIPS.md) | Locks, pins, and package relationships |

**Baseline:** tag `phase-3f-qualified` → `0a2af49ee86451c374a600579d3644c811cd12c0`  
**Ops companion:** `docs/operations/`  
**Legacy overview:** `docs/ARCHITECTURE.md` (Phase 1 framing; this package supersedes cloud-era detail)
