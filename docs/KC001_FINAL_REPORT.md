# KC-001 Final Report — GPT-OSS Native Vision Audit

**Branch:** `kc-001-gpt-oss-vision-audit`  
**Date:** 2026-07-23  
**Production impact:** None (Cobra Computer routing untouched)

---

## Executive summary

KC-001 reconstructed and audited a **native vision path into GPT-OSS**: SigLIP → PseudoDeepStack multi-depth features → MLP projector → GPT-OSS-compatible embeddings → MoE LM forward.  

On the available **RTX 4070 12GB** host, full `openai/gpt-oss-20b` weights could not be validated end-to-end (needs ~16GB+ MXFP4). Architecture, gradients, overfit, image-dependence, MoE instrumentation, licenses, datasets, API/benchmark contracts, and security limits were validated on a **GPT-OSS-shaped Tiny MoE surrogate** with the same injection contract.

**FINAL STATUS: B. KC-001 PARTIAL — ARCHITECTURE WORKS, FURTHER TRAINING REQUIRED**

(Not A: real GPT-OSS weights + real SigLIP encode-to-generate not completed on this GPU.  
Not C: no hard license veto for research path; Apache GPT-OSS + SigLIP usable with conditions.  
Not D: GPT-OSS foundation remains preferred over abandoning for a different base.)

### Supersession note (KC-002)

Deferred real-weight items from KC-001 are tracked under branch `kc-002-real-weight-validation`.  
As of 2026-07-23, KC-002 is **C. BLOCKED** on CUDA/VRAM/disk/cloud credentials — see `docs/KC002_FINAL_REPORT.md`.  
KC-001 surrogate results remain valid for architecture/contract proofs only; they do **not** satisfy KC-002.

---

## Exact upstream sources

| Component | ID |
|-----------|-----|
| LM | `openai/gpt-oss-20b` (Apache 2.0) |
| Vision reference | `vincentkaufmann/gpt-oss-20b-vision-preview` (architecture study) |
| Encoder | `google/siglip-so400m-patch14-384` |
| Alt multimodal | `OpenGVLab/InternVL3_5-GPT-OSS-20B-A4B-Preview` (license **D**) |

---

## License status

See `KC001_LICENSE_AUDIT.md`.

- GPT-OSS: **A**  
- SigLIP: **B** (WebLI residual risk)  
- Community vision data recipes (LLaVA/Infinity-MM): **D** for commercial training  
- KC-001 synthetic data: **A**

Weights were **not** redistributed in-repo.

---

## Reproduced architecture

Documented in `KC001_ARCHITECTURE.md`. Code: `kc001/src/cobra_kc001/`.

Native definition (`KC001_NATIVE_VISION_DEFINITION.md`) is satisfied **on the surrogate**: pixels → encoder features → projector → `inputs_embeds` into MoE LM → text logits, with trainable projector (+ attention LoRA-style unfreeze).

---

## Trainable parameters (surrogate configs)

| Config | Meaning |
|--------|---------|
| A | Projector only |
| B | Projector + attention |
| C | Projector + attention + router |
| D | Broader SFT (encoder frozen) |

Exact counts emitted by `trainable_map()` during `make overfit`.

---

## MoE routing findings

See `KC001_MOE_ROUTING_AUDIT.md`. Surrogate confirms image tokens alter router inputs; community evidence says projector-only fails on real GPT-OSS MoE — **QLoRA required**. No router surgery performed.

---

## Environment

| Item | Value |
|------|--------|
| Package | `kc001/` (`cobra-kc001`) |
| Python | 3.11–3.13 |
| GPU | RTX 4070 12GB |
| Lock | `kc001/requirements.lock` |
| Docker | `kc001/Dockerfile` |

---

## Experiments

| Experiment | Result |
|------------|--------|
| Unit tests | **16 passed** |
| Remote GPT-OSS config | **loaded** (`hidden=2880`, `layers=24`, `experts=32`, `vocab=201088`) |
| Overfit | loss 6.73 → 0.77 in 80 steps; **train_acc 1.0** (CPU surrogate) |
| Image dependence | **PASS** — correct logp (−0.62) ≫ wrong (−6.49) / noise (−6.08); none mismatched |
| Text regression | Surrogate smoke deterministic; real GPT-OSS weights deferred (VRAM + CPU torch wheel) |
| Performance | `KC001_PERFORMANCE.md` |

Artifacts: `kc001/artifacts/experiments/*.json` (gitignored).

---

## Dataset / security

- Datasets: audit only; synthetic used for proofs (`KC001_DATASET_AUDIT.md`).  
- Safety: byte/pixel/format limits; EXIF stripped (`cobra_kc001.safety`).  

---

## Costs

| Item | Estimate |
|------|----------|
| KC-001 local compute | &lt;1 GPU-hour |
| Finish community-style 20B vision train | ~$500–$3k (external reports) — **not started** |
| Large-scale Cobra train | **Not authorized in KC-001** |

---

## Unresolved risks

1. 12GB VRAM blocks real GPT-OSS validation.  
2. Dataset licenses for any LLaVA/Infinity-MM-style recipe.  
3. MoE routing adaptation quality unknown on real weights.  
4. Text regression under vision LoRA unknown.  
5. Trademark / attribution hygiene when branding Cobra Core.

---

## Recommended KC-002 direction

1. Rent / use ≥24GB (preferably 40GB+) GPU.  
2. Load `openai/gpt-oss-20b` + SigLIP; run real text baseline T1–T5.  
3. Train projector + QLoRA on **legally cleared** micro-set; repeat overfit + image-dependence on **real** weights.  
4. Instrument real MoE routers.  
5. Keep production on provider vision until gates pass.  
6. Do not ship Benchmark Lab adapter until gates in `KC001_BENCHMARK_INTEGRATION_PLAN.md` pass.

---

## Success criteria scorecard

| Criterion | Status |
|-----------|--------|
| Exact GPT-OSS base identified | ✔ |
| Licenses audited | ✔ |
| Reproducible environment | ✔ |
| Image encoder output verified | ✔ surrogate / stub (+ real SigLIP optional when downloaded) |
| Projector implemented + tested | ✔ |
| Image embeddings enter GPT-OSS path | ✔ surrogate `inputs_embeds` |
| Gradients reach trainable params | ✔ |
| Tiny overfit | ✔ (CLI) |
| Image dependence | ✔ (CLI) |
| Text regression real weights | ✖ deferred (VRAM) |
| MoE routing measured | ✔ surrogate; real deferred |
| Performance documented | ✔ |
| No production routing change | ✔ |
| No large-scale training | ✔ |
