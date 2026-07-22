# Phase 2E Diagnostics Runbook (Deferred Live Cohorts)

Use this when re-attempting the **bounded** Qwen3-8B diagnostic suite after Phase 2E static closure.

Closing GPU-heavy applications **does not guarantee** a successful model load. Stop after another access violation; do not repeatedly retry.

## Prerequisites

- Phase 2D baseline remains locked (`evaluations/baselines/qwen3-8b-cobrabench-v0.1.json`).
- Blocked run record preserved: `evaluations/analysis/phase2e-blocked-diagnostic-run.json` (`20260722T220000Z-2ediag01`).
- Use a **new** run ID for any live execution.
- Do not write into the locked Phase 2D result directory.
- Do not treat diagnostic outputs as official CobraBench v0.1 scores.

## Steps

1. **Close GPU-heavy applications** (games, browsers with hardware acceleration, other ML loads) when practical.
2. **Inspect GPU processes** (e.g. `nvidia-smi`) and note what still holds VRAM.
3. **Confirm available VRAM** — prefer several free GB above the ~7.5 GB typical 4-bit Qwen3-8B footprint (headroom matters).
4. **Confirm available system RAM** — avoid loading when free RAM is near single-digit GB.
5. **Run a minimal Qwen3-8B load check** (existing smoke/load path for the verified 8B artifact) before the full 25-job suite.
6. **Run diagnostics with a new run ID:**

```bash
python scripts/run_phase2e_diagnostics.py --run-id <new-run-id>
```

Optional dry-run first:

```bash
python scripts/run_phase2e_diagnostics.py --dry-run --run-id <new-run-id>
```

7. **Preserve the prior blocked-run record** — do not delete or overwrite `20260722T220000Z-2ediag01` metadata under analysis/.
8. **Stop on another `0xC0000005`** — record hardware state; do not loop load retries.
9. **Do not repeatedly retry model loads** in the same contended session.
10. **Generate cohort comparison reports only from completed outputs** — never fabricate thinking/cap/prompt/delimiter/stability deltas.

## After a successful run

- Keep `not_official_cobrabench: true` on all diagnostic artifacts.
- Fill deferred reports from real responses only.
- Revisit ADR-0004 Class 4 eligibility only if weaknesses persist after Class 1–3 controls.
