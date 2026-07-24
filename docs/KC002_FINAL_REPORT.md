# KC-002 Final Report — Real-Weight Validation

**Branch:** `kc-002-real-weight-validation`  
**Base branch:** `kc-001-gpt-oss-vision-audit`  
**Starting commit:** `e290292ab6ac877009c7290c1a9008b467466667`  
**Date:** 2026-07-23  

---

## FINAL STATUS

# C. KC-002 BLOCKED — HARDWARE, SOFTWARE, OR LICENSE BARRIER

Primary blockers (local execution host):

1. **PyTorch CPU-only** (`2.13.0+cpu`, `torch.cuda.is_available()==False`)  
2. **VRAM** RTX 4070 **12GB** &lt; required **24GB**  
3. **Disk** ~**8.5GB** free — cannot store GPT-OSS-20B + SigLIP caches  
4. **No cloud GPU credentials** in environment (RunPod/Lambda/Vast/Stripe Projects unavailable)

License barrier for synthetic micro-data: **none** (Apache-2.0 original synthetics).

---

## What shipped despite the block

| Deliverable | Location |
|-------------|----------|
| CUDA/VRAM hard gates | `kc002/src/cobra_kc002/env_gate.py` |
| Cost ceiling meter ($100 / 8h) | `kc002/src/cobra_kc002/cost.py` + `docs/KC002_COMPUTE_BUDGET.md` |
| Real GPT-OSS+SigLIP+PseudoDeepStack+projector+QLoRA loader | `kc002/src/cobra_kc002/real_model.py` |
| CLI gates (validate/text/siglip/forward/overfit/…) | `kc002/src/cobra_kc002/cli.py` |
| Legally cleared micro-dataset (32 items) | `data/kc002/` |
| Unit tests (env gate, dataset, projector dims) | `kc002/tests/` |
| Cloud runbook | `kc002/scripts/cloud_runbook.md` |

Surrogate paths are **rejected** when `COBRA_ALLOW_SURROGATE=0` (default).

---

## Decision gate answers (current)

| # | Question | Answer |
|---|----------|--------|
| 1 | Can real GPT-OSS consume projected SigLIP embeddings? | **Unknown — not run** |
| 2 | Can real model overfit image-grounded examples? | **Unknown — not run** |
| 3 | Correct-image ≫ wrong-image? | **Unknown — not run** |
| 4 | QLoRA preserves text? | **Unknown — not run** |
| 5 | Router adaptation required? | **Unevaluated on real weights** |
| 6 | Inference GPU | Estimate ≥16–24GB (unmeasured) |
| 7 | Training GPU | Estimate ≥24–48GB (unmeasured) |
| 8 | Measured cost | **$0** (no rental) |
| 9 | Dataset licenses clean? | **Yes** (synthetic Apache-2.0) |
| 10 | Architecture worth scaling? | **Still promising per KC-001; unproven on real weights** |

---

## Required next action (operator)

1. Rent a **≥24GB** (prefer 40–48GB) CUDA GPU within the `$100` / 8h ceiling.  
2. Attach ≥100GB disk; install CUDA PyTorch.  
3. Clone this branch; follow `kc002/scripts/cloud_runbook.md`.  
4. Execute: `validate-env → text-baseline → siglip → forward-gate → overfit → dependence → regression → moe`.  
5. Fill remaining KC002 docs from artifacts; re-grade toward **A** or **B** / **D**.

---

## Production impact

**None.** Cobra Computer routing unchanged. No model deployed. No large-scale training started. No uncleared datasets used.

---

## Success criteria scorecard

| Criterion | Status |
|-----------|--------|
| CUDA PyTorch verified | ✖ fail local |
| GPT-OSS real text | ✖ blocked |
| Real SigLIP | ✖ blocked |
| Real inputs_embeds path coded | ✔ (unexecuted) |
| Forward gate | ✖ blocked |
| Gradients projector/LoRA | ✖ blocked |
| Real overfit | ✖ blocked |
| Image dependence | ✖ blocked |
| Text regression | ✖ blocked |
| MoE measured | ✖ blocked |
| Budget respected | ✔ $0 ≤ $100 |
| Dataset provenance | ✔ |
| Production untouched | ✔ |
