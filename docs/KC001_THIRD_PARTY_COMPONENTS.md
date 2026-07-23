# KC-001 — Third-Party Components

Inventory of upstream components proposed for GPT-OSS native vision reproduction.  
Weights are **referenced by ID**, not vendored.

---

## Language model

| Item | Value |
|------|--------|
| Name | GPT-OSS-20B |
| URL | https://huggingface.co/openai/gpt-oss-20b |
| Org | OpenAI |
| Architecture | `GptOssForCausalLM` / `gpt_oss` |
| Params (card) | ~21B total MoE |
| Active experts / token | 4 of 32 local experts |
| Hidden size | 2880 |
| Layers | 24 |
| Vocab | 201088 |
| Context | max_position_embeddings 131072 (YaRN); initial 4096 |
| Quantization | MXFP4 native |
| License status | **A** (Apache 2.0) |
| KC-001 use | Baseline text validation target; integration dims |

Sibling: `openai/gpt-oss-120b` (~117B) — out of scope for local 12GB GPU.

---

## Community vision reference (architecture only)

| Item | Value |
|------|--------|
| Name | GPT-OSS-20B-Vision Preview |
| URL | https://huggingface.co/vincentkaufmann/gpt-oss-20b-vision-preview |
| Author | Vincent Kaufmann |
| Method | PseudoDeepStack (layers 9/18/27 concat → MLP) |
| Projector | `Linear(3456→2880) → GELU → Linear(2880→2880)` (~18.2M) |
| Visual tokens | 729 (27×27 @ 384, patch 14) |
| Adaptation | QLoRA r=128 α=256 |
| License status | **B** study / **D** if training on listed datasets |
| KC-001 use | Reconstruct architecture; **do not redistribute weights** |

---

## Image encoder

| Item | Value |
|------|--------|
| Name | SigLIP So400M patch14-384 |
| URL | https://huggingface.co/google/siglip-so400m-patch14-384 |
| Vision hidden | 1152 |
| Layers | 27 |
| Image size | 384 |
| Patch size | 14 |
| Tokens | (384/14)² = 729 |
| License status | **B** |

---

## Training / PEFT stack

| Component | Typical pin | License status |
|-----------|-------------|----------------|
| PyTorch | ≥2.4 | A |
| transformers | ≥4.55 (gpt_oss support) | A |
| accelerate | latest compatible | A |
| peft | latest compatible | A |
| bitsandbytes | optional QLoRA | B |
| flash-attn | optional; may be unavailable on Windows | B / skip |

---

## Dataset references (not downloaded in bulk)

| Dataset | URL | License status |
|---------|-----|----------------|
| LLaVA-Instruct-150K | https://huggingface.co/datasets/liuhaotian/LLaVA-Instruct-150K | D |
| Infinity-MM | https://huggingface.co/datasets/BAAI/Infinity-MM | D |
| KC-001 synthetic | `kc001/data/synthetic/` | A |

---

## Alternative multimodal bases (decision matrix)

| Name | URL | Notes |
|------|-----|-------|
| InternVL3.5-GPT-OSS-20B | https://huggingface.co/OpenGVLab/InternVL3_5-GPT-OSS-20B-A4B-Preview | Full-stack VLM; license **D** pending pin |
| Qwen2.5-VL / Qwen3-VL family | Hugging Face | Different LM foundation; higher maturity VL |

---

## Attribution (minimal NOTICE sketch)

When distributing Cobra Core Vision derivatives, retain at least:

- OpenAI GPT-OSS Apache 2.0 NOTICE / LICENSE  
- Google SigLIP Apache 2.0 attribution  
- Transformers / PyTorch notices  
- Method citation if PseudoDeepStack design is used: Kaufmann 2026 GPT-OSS-Vision card  

Do **not** imply OpenAI endorsement of Cobra Core.
