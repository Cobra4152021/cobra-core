# KC-001 — License Audit

**Phase:** KC-001  
**Rule:** Do not rely on README claims alone. Inspect LICENSE / NOTICE / model card / dataset card.  
**KC-001 policy:** Do not rebrand or redistribute upstream weights during this phase.

Status codes:

| Code | Meaning |
|------|---------|
| **A** | ACCEPTABLE FOR COMMERCIAL RESEARCH |
| **B** | ACCEPTABLE WITH CONDITIONS |
| **C** | RESEARCH-ONLY |
| **D** | UNCLEAR — LEGAL REVIEW REQUIRED |
| **E** | NOT ACCEPTABLE |

---

## 1. GPT-OSS-20B (language foundation)

| Field | Record |
|-------|--------|
| Repository / hub | https://huggingface.co/openai/gpt-oss-20b |
| Organization | OpenAI |
| Identified artifact | `openai/gpt-oss-20b` (MXFP4 open weights) |
| Config SHA source | Live `config.json` fetched 2026-07-23 (architecture `GptOssForCausalLM`) |
| Software / weights license file | Apache License 2.0 (`LICENSE` on hub) |
| Model card claim | Apache 2.0; commercial use permitted under Apache terms |
| Training-data license statements | OpenAI model card describes training techniques; **full training-data inventory is not published as a redistributable dataset** |
| Commercial-use | Permitted under Apache 2.0 (copyright + patent grants with standard termination) |
| Redistribution | Allowed if Apache §§4 conditions met (license copy, change notices, NOTICE retention) |
| Attribution | Retain copyright / NOTICE as required |
| Derivative works | Allowed; modifications must carry notices |
| Trademark | Apache §6 — no trademark license for “OpenAI” / product names |
| Known patent concerns | Apache patent grant + litigation termination; no specific third-party patent clearance found in LICENSE |
| Unresolved legal questions | (1) Training-data provenance for downstream products. (2) Whether MXFP4 weights + community LoRA merges create additional NOTICE obligations. |
| **Status** | **A** for research and commercial *use/derivation of weights under Apache 2.0*; training-data provenance remains a product-risk topic (document, do not treat as cleared). |

Also noted: `openai/gpt-oss-120b` — same license family (Apache 2.0) per OpenAI announcement; not loaded in KC-001.

---

## 2. GPT-OSS inference / Transformers implementation

| Field | Record |
|-------|--------|
| Upstream | Hugging Face `transformers` (`GptOssForCausalLM`) |
| License | Apache 2.0 (transformers) |
| Commit / pin | Pin in `kc001/pyproject.toml` / lockfile |
| **Status** | **A** |

Official OpenAI reference tooling (if used): verify per-repo LICENSE before vendoring. KC-001 uses Transformers APIs only.

---

## 3. Tokenizer

| Field | Record |
|-------|--------|
| Source | Shipped with `openai/gpt-oss-20b` (vocab_size **201088** per config) |
| License | Covered by model Apache 2.0 distribution |
| **Status** | **A** with Apache redistribution conditions |

---

## 4. SigLIP image encoder

| Field | Record |
|-------|--------|
| Hub | https://huggingface.co/google/siglip-so400m-patch14-384 |
| Org | Google (weights); paper Zhai et al. |
| Model card license tag | `apache-2.0` |
| Code origin | big_vision / Transformers SigLIP |
| Training data | WebLI (Chen et al., 2023) — **web-scale scraped image–text**; provenance incomplete for all samples |
| Commercial-use of weights | Apache 2.0 on card; **WebLI content rights are not individually cleared** |
| Patent / trademark | No separate patent grant beyond Apache; “SigLIP” naming is descriptive |
| Unresolved | Web-scraped pretraining data residual risk for some jurisdictions / verticals |
| **Status** | **B** — acceptable for commercial research with conditions: retain Apache notices; product counsel should review WebLI residual-risk posture before consumer deployment |

---

## 5. Community GPT-OSS-20B-Vision (PseudoDeepStack reference)

| Field | Record |
|-------|--------|
| Hub | https://huggingface.co/vincentkaufmann/gpt-oss-20b-vision-preview |
| Author | Vincent Kaufmann |
| Card license | Apache 2.0 |
| Base model | `axolotl-ai-co/gpt-oss-20b-dequantized` (derivative of GPT-OSS) |
| Vision | SigLIP + custom projector checkpoint (`projector-step9000.pt`) |
| Training data listed | LLaVA-Instruct-150K; Infinity-MM Stage 4 |
| Redistribution in KC-001 | **Not redistributing** weights; architecture reproduced from public model card + usage snippet |
| Trademark | Do not present as official OpenAI multimodal product |
| Unresolved | (1) LLaVA / Infinity-MM dataset licenses for *training Cobra weights*. (2) Completeness of Apache notices in merged LoRA checkpoint. (3) Author attribution for PseudoDeepStack method if code is copied. |
| **Status** | **B** for studying/reproducing architecture; **D** before shipping any weights trained on the listed datasets without dataset-level clearance |

---

## 6. OpenGVLab InternVL3.5-GPT-OSS-20B (alternative multimodal base)

| Field | Record |
|-------|--------|
| Hub | https://huggingface.co/OpenGVLab/InternVL3_5-GPT-OSS-20B-A4B-Preview |
| Org | OpenGVLab / Shanghai AI Lab |
| License | **Must re-check** model card LICENSE at KC-002 selection time (often research / custom) |
| **Status** | **D** until LICENSE file is pinned and reviewed for commercial use |

---

## 7. LoRA / QLoRA stack

| Component | License | Status |
|-----------|---------|--------|
| PEFT | Apache 2.0 | **A** |
| bitsandbytes | MIT / CUDA binary terms — verify installed version NOTICE | **B** |
| Accelerate | Apache 2.0 | **A** |
| PyTorch | BSD-style | **A** |

---

## 8. Datasets (audit only — not bulk-downloaded in KC-001)

| Dataset | Card notes | Status |
|---------|------------|--------|
| LLaVA-Instruct-150K | Built on COCO / GPT-generated instructions; mixed terms | **D** for commercial training |
| Infinity-MM (BAAI) | Large mix; check per-subset licenses | **D** |
| COCO captions | Research use common; commercial needs care | **B/D** by use case |
| Synthetic procedural images (KC-001 overfit) | Generated in-repo | **A** |

See `KC001_DATASET_AUDIT.md`.

---

## 9. Evaluation tools

| Tool | Status |
|------|--------|
| pytest | MIT — **A** |
| Pillow | HPND-like — **A** |
| In-repo KC-001 eval metadata | Apache/MIT intended for Cobra Core — **A** |

---

## Summary matrix

| Component | Status |
|-----------|--------|
| GPT-OSS-20B / 120B weights | **A** |
| Transformers GPT-OSS code | **A** |
| Tokenizer | **A** |
| SigLIP-SO400M | **B** |
| Kaufmann vision preview (study) | **B** (arch) / **D** (train on listed data) |
| InternVL3.5-GPT-OSS | **D** |
| PEFT / Accelerate / Torch | **A** / **B** (bnb) |
| LLaVA-Instruct / Infinity-MM | **D** |
| KC-001 synthetic overfit data | **A** |

---

## KC-001 legal constraints (operational)

1. Do **not** commit or redistribute upstream model weights in this repo.  
2. Do **not** rebrand GPT-OSS or SigLIP as “Cobra” weights.  
3. Prefer synthetic / clearly licensed micro-sets for overfit proofs.  
4. Escalate any commercial training plan on LLaVA/Infinity-MM/WebLI-derived stacks to legal review (**D**).  
