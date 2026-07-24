# Phase 4.2 — Controlled Pilot Validation Results

**Status:** Executed  
**Product baseline:** `14c1ada5433777b6e2dd126e7f0fd2c80aefa60c`  
**Software pins:** `phase-3f-qualified` equivalence (torch/transformers/bnb/Python)  
**Host SKU:** NVIDIA RTX A5000 @ $0.16/hr (Community; L4/A40 unavailable at create time)  
**CobraBench:** not run (`prepared-not-run`)  
**Official score:** **0.840** (unchanged)

## 1. Mission outcome

The Phase 4 framework is **practical enough to proceed**, with documented revisions before a full 46-task run. Pilot pass rate **100%** (Pass/Pass+); **0** critical hard fails.

## 2. Tasks executed

| # | Task | Domain | Result |
| ---: | --- | --- | --- |
| 1 | INV-05 | Investigator | Pass |
| 2 | INV-08 | Investigator | Pass+ |
| 3 | RS-05 | Research | Pass+ |
| 4 | RS-06 | Research | Pass+ |
| 5 | REL-01 | Reliability | Pass+ (3 identical repeats) |
| 6 | REL-04 | Reliability | Pass |
| 7 | CG-01 | Engineering | Pass+ |
| 8 | CG-12 | Engineering | Pass+ |
| 9 | BZ-03 | Business | Pass |
| 10 | BZ-05 | Business | Pass (truncated) |

## 3. Cloud runtime

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud |
| Primary pod | `q5s51eej16q58m` |
| GPU | NVIDIA RTX A5000 (24 GB class) |
| Image | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` |
| Python | 3.12.3 |
| torch | 2.6.0+cu124 |
| transformers / accelerate / bnb | 5.14.1 / 1.14.0 / 0.49.2 |
| Quant path | 4-bit NF4 double, float16, `device_map={"": 0}` |
| Model revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Peak VRAM | ~6.35 GiB |
| Cleanup | Pod deleted (HTTP 204); zero remaining pods |

**Equivalence note:** Software stack matches Phase 3F pins. Host GPU is A5000 (authorized fallback class), not the A40 used for Outcome A. This pilot does **not** replace A40 qualification; it validates framework practicality on a pin-equivalent stack.

## 4. Elapsed time & cost

| Segment | Estimate |
| --- | --- |
| Primary pod wall clock | ~0.77 h (bring-up + download + install + pilot) |
| Inference-only (RUN.json) | ~110 s load+generate window |
| Primary pod cost | ~$0.12 @ $0.16/hr |
| Failed short pods (3090×2) | ~$0.02 |
| **Total estimated** | **~$0.14** |
| Ceiling | $10 respected |

## 5. Evidence location

```text
evaluations/diagnostics/phase-4-2-pilot/
  RUN.json (via remote/pilot-out/RUN.json)
  remote/pilot-out/tasks/<TASK_ID>/{prompt,output_*,metrics}.json
  cost-record.json
  pod-meta.json
docs/capability-validation/pilot/
  PILOT_RESULTS.md
  PILOT_SCORECARD.md
  LESSONS_LEARNED.md
  FRAMEWORK_REVISIONS.md
```

## 6. Recommendation

**Proceed to full Phase 4** after applying the revisions listed in `FRAMEWORK_REVISIONS.md` (fixture packaging, token budgets, scoring notes, automation hardening). Do **not** treat this pilot as Beta gate completion (n=10 only; host SKU ≠ A40).

## 7. Integrity

- No CobraBench cases  
- No prompt tuning during pilot  
- No training / deployment / model replacement  
- Score **0.840** unchanged  
