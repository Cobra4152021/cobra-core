# Capability Validation Report — Phase 4 Full

**Status:** Executed (framework frozen; no mid-run prompt/runtime/dependency changes)  
**Date:** 2026-07-24  
**Software pins:** `phase-3f-qualified` equivalence  
**Official CobraBench v0.1 score:** **0.840** (unchanged)  
**CobraBench v0.2-rc2:** `prepared-not-run`  
**Pilot baseline:** Phase 4.2 successful  

## 1. Executive summary

| Metric | Result |
| --- | --- |
| Tasks executed | **46 / 46** |
| Execution success (non-empty outputs) | **46 / 46** |
| Overall Pass or Pass+ rate | **97.8% (45/46)** |
| Critical hard fails | **0** |
| GPU | NVIDIA GeForce RTX 3090 |
| Elapsed (pod wall) | **0.4209 h (~25.3 min)** |
| Estimated cloud cost | **$0.0926** @ $0.22/hr |
| Cleanup | Pod terminated (HTTP 204); **0** remaining pods |

### Final recommendation

# Ready for Beta

Justification: Beta gates in `docs/product/RELEASE_GATES.md` require executed capability validation, ≥90% Pass/Pass+, and no critical failures. All are met. Reliability domain still passes suite rules (REL-01 Pass+, ≥5/7 Pass/Pass+, REL-04 not hard-fail) despite one minor Marginal on REL-07.

Caveats (do not block Beta label, but require follow-up engineering):

- Host SKU was **RTX 3090**, not the Phase 3F A40 (software pins matched).
- REL-07 (large-context count) was truncated and incomplete (minor).
- This is **workload validation**, not an official CobraBench score.

---

## 2. Pass rate by domain

| Domain (report label) | Catalog domain key | Pass/Pass+ | Rate |
| --- | --- | ---: | ---: |
| Engineering | engineering | 15 / 15 | **100%** |
| Research | research | 8 / 8 | **100%** |
| Investigator | investigator | 8 / 8 | **100%** |
| Business | business | 8 / 8 | **100%** |
| Reliability | reliability | 6 / 7 | **85.7%** |
| **Overall** | | **45 / 46** | **97.8%** |

---

## 3. Failures (complete list)

Only one task failed to reach Pass/Pass+:

| Task | Grade | Severity | Classification rationale |
| --- | --- | --- | --- |
| **REL-07** | Marginal | **minor** | Large-context marker count: listed many line indices but truncated before stating the integer **29**; incomplete method/answer. Not a grounding/safety hard fail. |

No **critical**, **major**, or **cosmetic** failures recorded.

### Critical failures

*None.*

---

## 4. Cloud runtime & telemetry

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud |
| Pod ID | `s4qjueg403fjks` |
| GPU | NVIDIA GeForce RTX 3090 |
| Hourly rate | $0.22 |
| Image | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` |
| Python | 3.12.3 |
| torch | 2.6.0+cu124 |
| transformers / bitsandbytes | 5.14.1 / 0.49.2 |
| Quant / device_map | 4-bit NF4 double, float16, `{"": 0}` |
| Model revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Peak VRAM | 7,073,232,896 bytes (~6.59 GiB) |
| Model load | 6.95 s (warm-ish after install imports) |
| Integrity | No CobraBench; no prompt tuning; no training; no deployment |

Evidence root: `evaluations/diagnostics/phase-4-full/`

---

## 5. Per-task grades (compact)

| Task | Grade | Task | Grade | Task | Grade |
| --- | --- | --- | --- | --- | --- |
| CG-01 | Pass+ | CG-02 | Pass | CG-03 | Pass |
| CG-04 | Pass | CG-05 | Pass | CG-06 | Pass |
| CG-07 | Pass | CG-08 | Pass | CG-09 | Pass |
| CG-10 | Pass | CG-11 | Pass | CG-12 | Pass+ |
| CG-13 | Pass | CG-14 | Pass | CG-15 | Pass |
| RS-01 | Pass | RS-02 | Pass | RS-03 | Pass |
| RS-04 | Pass | RS-05 | Pass+ | RS-06 | Pass+ |
| RS-07 | Pass | RS-08 | Pass | INV-01 | Pass |
| INV-02 | Pass | INV-03 | Pass | INV-04 | Pass |
| INV-05 | Pass | INV-06 | Pass | INV-07 | Pass |
| INV-08 | Pass+ | BZ-01 | Pass | BZ-02 | Pass |
| BZ-03 | Pass | BZ-04 | Pass | BZ-05 | Pass |
| BZ-06 | Pass | BZ-07 | Pass | BZ-08 | Pass |
| REL-01 | Pass+ | REL-02 | Pass | REL-03 | Pass |
| REL-04 | Pass | REL-05 | Pass | REL-06 | Pass+ |
| REL-07 | **Marginal** | | | | |

Full machine-readable scores: `evaluations/diagnostics/phase-4-full/SCOREBOARD.json`.

---

## 6. Engineering recommendations (post-completion only)

1. **Raise max tokens / require final numeric answer for REL-07** (and similar aggregation tasks) so truncation cannot omit the count.  
2. **Ship gold expected values** in fixtures (needle string, marker count=29, contradiction pairs).  
3. **Prefer L4/A5000 when capacity allows**; record SKU vs Phase 3F A40 explicitly in Beta evidence (already done here).  
4. **CG-10/CG-11:** add objective checks for module-worker vs legacy `addEventListener` style.  
5. **Apply Phase 4.2 framework revisions** (fixtures, budgets, SSH harness) before RC repeat-validation.  
6. **Do not** convert these grades into official **0.840** updates; keep CobraBench separately authorized.

---

## 7. Integrity attestation

- Framework not modified during execution.  
- Runtime pins not changed.  
- Dependencies not upgraded beyond pinned install.  
- No benchmark execution; no training; no deployment.  
- Cloud resources terminated after export.
