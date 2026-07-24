# Future automation plan — Phase 4 Capability Validation

**Do not implement in the framework-only phase.** This is a roadmap for a later authorized engineering effort.

## 1. Goals

1. Reduce human time per task while keeping humans on grounding/safety judgments.
2. Make runs reproducible (fixture hashes, pin checks, structured scores).
3. Keep automation **separate** from CobraBench evaluators (different schemas/purposes).

## 2. Phased automation

### A0 — Prep (no GPU)

| Work | Output |
| --- | --- |
| Author synthetic fixtures under `evaluations/fixtures/capability-validation/` (git policy permitting) | Hashed inputs |
| JSON Schema for `score.json` / `SUITE_SUMMARY.json` | Schemas + examples |
| CLI: list tasks, validate catalog IDs | `scripts/capability_validation_ctl.py` (future) |

### A1 — Harness (GPU; authorized spend)

| Work | Output |
| --- | --- |
| Runner invokes locked runtime profile | Per-task `output.txt` + telemetry |
| Enforce fresh process for REL-* | Process isolation |
| Pin check via `phase3g_verify_env.py` before batch | Abort on drift |

### A2 — Objective checks (CPU)

| Check | Tasks helped |
| --- | --- |
| JSON parse / schema validate | RS-07, structured outputs |
| Citation ID allowlist regex | RS-05, INV-* |
| SQL parse soft-check (sqlparse) | CG-06 |
| TypeScript/Python syntax compile where available | CG-* subset |
| Exact needle match | REL-06, REL-07 |

Objective checks **never** fully replace human U3/U4 scoring.

### A3 — Human scoring UI / checklist

| Work | Output |
| --- | --- |
| Score sheet generator from rubric dimensions | Markdown or simple form |
| Diff viewer for REL-01 triples | Stability assist |

### A4 — Reporting

| Work | Output |
| --- | --- |
| Aggregate domain/suite gates | `SUITE_SUMMARY.json` |
| Hash manifest | `SHA256SUMS` |
| Optional export into `docs/releases/` only under freeze authorization | Release package |

## 3. Non-goals for automation

- Auto-tuning prompts to raise grades
- Merging results into official **0.840**
- Training reward models on this suite without separate ethics/tech review
- Browser login automation to cloud consoles

## 4. Estimated automation effort (future)

| Phase | Effort |
| --- | --- |
| A0 | 1–2 engineer-days |
| A1 | 2–4 engineer-days + cloud session |
| A2 | 2–3 engineer-days |
| A3 | 1–2 engineer-days |
| A4 | 1 engineer-day |

## 5. Trigger to start automation

Only after:

1. Manual pilot of ≥10 tasks validates fixtures/rubric, **or**
2. Explicit authorization to build the harness before pilot

## 6. Interface sketch (informative)

```text
cobra-capability-validate --task CG-01 --outdir evaluations/diagnostics/phase-4-...
cobra-capability-score --task CG-01 -- Rubric dimensions via stdin/file
cobra-capability-summary --run <dir>
```

Names are provisional; match existing `cobra_*` CLI style when implemented.
