# KC-001 — GPT-OSS Baseline

## Identified base model

| Field | Value |
|-------|--------|
| Hub ID | `openai/gpt-oss-20b` |
| Architecture | `GptOssForCausalLM` / `gpt_oss` |
| License | Apache 2.0 |
| Quantization | MXFP4 (native) |
| Total params (public cards) | ~21B MoE |
| Active experts / token | 4 |
| Local experts | 32 |
| Layers | 24 |
| Hidden size | 2880 |
| Intermediate size | 2880 |
| Attention heads | 64 (KV heads 8) |
| Head dim | 64 |
| Vocab size | 201088 |
| Max position embeddings | 131072 (YaRN; initial context 4096) |
| Sliding window | 128 (alternating sliding/full attention layers) |
| Supported precision | MXFP4 weights; bf16/fp16 compute in Transformers stacks |
| Min practical inference HW | **~16GB** for 20B MXFP4 (OpenAI); BF16 merge ~40GB (vision preview note) |

Sibling: `openai/gpt-oss-120b` (~117B) — single ~80GB GPU class.

---

## Local host (KC-001 measurement machine)

| Field | Value |
|-------|--------|
| OS | Windows 10 (build 22621) |
| GPU | NVIDIA GeForce RTX 4070 **12GB** |
| CUDA (driver) | 13.3 (UMD) / nvidia-smi 610.74 |
| nvcc | not installed |
| Python | 3.13.5 |

**Implication:** Full GPT-OSS-20B load is **not reliable** on this GPU. KC-001 validates:

1. Remote `AutoConfig` for `openai/gpt-oss-20b` (architecture facts).  
2. Deterministic text path on **Tiny GPT-OSS-shaped MoE** surrogate.  
3. Native vision injection path on the surrogate.

Full-weight text smoke is deferred to a ≥16GB (preferably 24–48GB) machine / cloud GPU.

---

## Baseline text prompts (preserved for regression)

These prompts are frozen for KC-001/KC-002 text regression. Outputs on the **surrogate** are not semantically meaningful; on real GPT-OSS they must be captured when hardware allows.

| ID | Prompt |
|----|--------|
| T1 | `Say the word "ok" and nothing else.` |
| T2 | `What is 17+4? Reply with only the number.` |
| T3 | `Translate to French: good morning` |
| T4 | `Write a JSON object with keys a=1 and b=2 only.` |
| T5 | `List three primary colors as a comma-separated list.` |

### Surrogate smoke (executed in KC-001)

See `kc001` CLI `smoke-text`:

- tokenizer/config: real config fetch attempted  
- deterministic forward: required pass on tiny LM  
- latency / VRAM: recorded in CLI JSON  

### Real-weight outputs

**Status:** Not captured on RTX 4070 12GB in this phase.  
**Placeholder artifact path:** `kc001/artifacts/baseline_text_real.json` (create when run on adequate GPU).

---

## Attention implementation notes

- Layer types alternate `sliding_attention` / `full_attention`.  
- `output_router_logits` default false — enable for MoE audits on real weights.  
- Flash-Attention: optional; often unavailable on Windows — document skip.

---

## Verdict for Step 4

| Check | Result |
|-------|--------|
| Exact base identified | **PASS** (`openai/gpt-oss-20b`) |
| Config loads | **PASS** (when network/HF available) |
| Tokenizer loads | **DEFERRED** (needs weight/tokenizer files) |
| Text generation real weights | **BLOCKED** by 12GB VRAM |
| Deterministic tiny surrogate | **PASS** via `make smoke-text` |
