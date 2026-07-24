# Recommended framework revisions (do not apply during pilot execution)

These changes are **recommended for a pre–full-Phase-4 docs update**. They were **not** applied while the pilot ran.

## R1 — Fixture packaging

- Add `evaluations/fixtures/capability-validation/pilot/` (or full suite) with per-task `prompt.md` + optional `gold.json`.
- Hash fixtures in a manifest; worker loads by task ID only.

## R2 — Generation budgets by task class

| Class | Suggested max_new_tokens |
| --- | ---: |
| Short grounded Q&A / REL | 128–256 |
| Investigator / Research structured | 384–512 |
| Code | 512–768 |
| Business runbook / architecture | 768–1024 |

Record the budget in task metadata so truncation is attributable.

## R3 — REL-01 process isolation

- Clarify: pilot may use in-process repeats; **full suite requires fresh OS process per repeat** (or document why not).
- Add optional objective equality check on normalized text.

## R4 — Gold keys for contradiction / citation tasks

- INV-05 / INV-06 / RS-05 / RS-06: ship expected citation allowlist + required contradiction pairs.
- Soft-fail vs hard-fail rules for extra spurious contradictions.

## R5 — Malformed-input scoring note

- REL-04: inventing a *hypothetical* fixed JSON example is **not** a hard fail if the model clearly rejects parsing the original; cap U3 at 2 if example fields are fabricated.

## R6 — Business checklist scoring

- BZ-03: required bullets (workspace path, torch index-url, inventory hash verification method, no CobraBench, terminate pod).
- Missing required bullet → max Pass (not Pass+).

## R7 — Automation / ops harness

- Prefer base64-wrapped remote scripts from Windows.
- Refresh SSH port every call.
- Disable inductor workers during env probes.
- Preflight: refuse create if any RUNNING pod exists; prefer L4 → A5000 → record actual SKU.
- Separate “bring-up” cost from “inference” cost in cost-record schema.

## R8 — Pilot vs full-suite reporting

- Add `run_kind: pilot|full` to suite summary schema.
- Beta gate (≥90%) applies only to **full** catalog execution on an authorized host class.

## Priority before full Phase 4

1. R1 fixtures + R2 budgets (blocking quality)  
2. R4 gold keys for INV/RS critical tasks  
3. R7 harness hardening  
4. R3/R5/R6 rubric clarifications (docs-only, fast)
