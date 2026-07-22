# Qwen Candidate Analysis (Phase 2A)

**Status:** Research / intake only. No weights downloaded.  
**Intake date:** 2026-07-22  
**Evidence standard:** Official Qwen docs, GitHub (`QwenLM/Qwen3`), Hugging Face `Qwen` org model cards / Hub API commits, official LICENSE files, arXiv technical reports.

> These category scores are **intake estimates**, not CobraBench results.

## Evidence legend

| Label | Meaning |
| --- | --- |
| **Verified** | Stated in an authoritative primary source cited below |
| **Estimate** | Calculated from verified parameters or labeled engineering judgment |
| **Assumption** | Working hypothesis for Cobra planning; not proven |
| **Unknown** | Not established from primary sources at intake time |

## Primary sources used

1. [QwenLM/Qwen3](https://github.com/QwenLM/Qwen3) — official GitHub README / release notes  
2. [Qwen Key Concepts](https://qwen.readthedocs.io/en/latest/getting_started/concepts.html) — official docs  
3. [Qwen Speed Benchmark](https://qwen.readthedocs.io/en/latest/getting_started/speed_benchmark.html) — official memory/speed tables  
4. Hugging Face model cards: `Qwen/Qwen3-32B`, `Qwen/Qwen3-8B`, `Qwen/Qwen3-4B`, `Qwen/Qwen3-14B`, `Qwen/Qwen3-30B-A3B-Instruct-2507`, `Qwen/Qwen3-30B-A3B-Thinking-2507`, `Qwen/Qwen2.5-Coder-32B-Instruct`, `Qwen/Qwen2.5-72B-Instruct`  
5. Hugging Face Hub API commit SHAs (retrieved 2026-07-22)  
6. [Qwen3 Technical Report](https://arxiv.org/abs/2505.09388)  
7. [Qwen2.5 Technical Report](https://arxiv.org/abs/2412.15115)  
8. Official `LICENSE` for `Qwen/Qwen3-32B` (Apache 2.0 text)

---

## Family overview (verified)

### Qwen3 (current generation)

- Dense sizes include 0.6B, 1.7B, 4B, 8B, 14B, 32B (**verified**: GitHub README / docs).  
- MoE sizes include 30B-A3B and 235B-A22B (**verified**).  
- Hybrid thinking / non-thinking in untitled (no `-Instruct`/`-Thinking`) checkpoints via `enable_thinking` (**verified**: model cards + docs).  
- Qwen3-2507 introduces separate `-Instruct-2507` and `-Thinking-2507` variants with native **262,144** context and optional **1M** path (**verified**: GitHub news + 2507 model cards).  
- Open-weight Qwen3 models are licensed under **Apache 2.0** (**verified**: GitHub License Agreement section + HF `license:apache-2.0` + LICENSE file).  
- Multilingual support: **100+** languages/dialects on model cards; docs also state **119** languages/dialects (**verified**, wording differs by page).  
- Tool / agent / MCP-oriented capabilities documented (**verified**: docs + model cards).  
- Official local/deploy paths include Transformers, vLLM, SGLang, llama.cpp, Ollama, LM Studio, MLX-LM (**verified**: docs / model cards).

### Qwen2.5 (prior generation, still relevant)

- Dense instruct sizes 0.5B–72B (**verified**: Qwen2.5 technical report).  
- `Qwen2.5-72B-Instruct` Hub card uses `license: other` / Qwen license (**verified**: HF API `cardData.license=other`) — **less suitable** for commercial clarity than Apache-2.0 Qwen3.  
- `Qwen2.5-Coder-32B-Instruct` is code-specialized (**verified**: model card tags / paper links).

---

## Candidate matrix

### 1) Qwen3-32B — **Selected primary baseline**

| Attribute | Value | Evidence class |
| --- | --- | --- |
| Exact model name | `Qwen3-32B` | Verified |
| Official repository | https://huggingface.co/Qwen/Qwen3-32B | Verified |
| Exact revision / commit | `9216db5781bf21249d130ec9da846c4624c16137` | Verified (HF API 2026-07-22) |
| Release / last modified | Hub `lastModified` 2025-07-26 | Verified |
| Architecture | Dense causal transformer-decoder | Verified |
| Total parameters | 32.8B (non-embedding 31.2B) | Verified (model card) |
| Active parameters | = total (dense) | Verified |
| Dense / MoE | Dense | Verified |
| Native context | 32,768 | Verified |
| Extended context | 131,072 via YaRN | Verified |
| Languages | 100+ / 119 dialects (docs) | Verified |
| Instruction-tuned | Yes (post-trained hybrid chat model) | Verified |
| Reasoning behavior | Hybrid thinking + non-thinking | Verified |
| Tool / function calling | Yes (Qwen-Agent / templates) | Verified |
| Structured output | Promptable; not a separate JSON-mode guarantee | Assumption |
| Multimodal | Text-only checkpoint | Verified |
| Quantization availability | Official BF16; community/official quant paths via docs (AWQ/GPTQ/GGUF guidance) | Verified (availability of methods); specific third-party quants not inventoried |
| VRAM (BF16, Transformers, short ctx) | ~62,751 MB | Verified (official speed benchmark) |
| Storage (BF16 weights) | ~66 GB | Estimate (≈2 bytes × 32.8B params) |
| CPU/RAM feasibility | Possible with heavy offload / llama.cpp quants; not practical for full BF16 CobraBench | Estimate |
| Inference speed | Official SGLang BF16 short-ctx ~20.7 tok/s on H20; Transformers lower | Verified (official table; hardware-specific) |
| LoRA / QLoRA suitability | Dense decoder; widely supported for PEFT | Assumption (framework support exists; Cobra has not fine-tuned) |
| License | Apache-2.0 | Verified |
| Redistribution / commercial | Apache-2.0 terms apply; preserve notices | Verified (license text) |
| Acceptable-use restrictions | Apache-2.0 (no separate Qwen proprietary AUP on this card) | Verified for license file; product ToS for hosted Qwen Chat is out of scope |
| Deployment limitations | Needs recent `transformers>=4.51`; thinking mode sampling guidance differs from greedy | Verified |
| Likely CobraBench strengths | Investigation reasoning, coding, tool use, long-doc (32K/YaRN), single-checkpoint thinking switch | Assumption |
| Likely CobraBench weaknesses | Hallucination/citation still unproven; thinking traces can inflate tokens/cost | Assumption / Unknown |

### 2) Qwen3-8B — **Selected resource-constrained baseline**

| Attribute | Value | Evidence class |
| --- | --- | --- |
| Exact model name | `Qwen3-8B` | Verified |
| Repository | https://huggingface.co/Qwen/Qwen3-8B | Verified |
| Commit | `b968826d9c46dd6066d109eabc6255188de91218` | Verified (HF API) |
| Parameters | 8.2B (non-embedding 6.95B) | Verified |
| Architecture | Dense hybrid thinking | Verified |
| Native / extended context | 32,768 / 131,072 YaRN | Verified |
| License | Apache-2.0 | Verified |
| VRAM (BF16 Transformers short ctx) | ~15,947 MB | Verified (official speed benchmark) |
| Storage (BF16) | ~16 GB | Estimate |
| Role fit | CI smoke, local iteration, regression loops | Assumption |

### 3) Qwen3-30B-A3B-Thinking-2507 — **Selected reasoning challenger (acquire after primary)**

| Attribute | Value | Evidence class |
| --- | --- | --- |
| Exact model name | `Qwen3-30B-A3B-Thinking-2507` | Verified |
| Repository | https://huggingface.co/Qwen/Qwen3-30B-A3B-Thinking-2507 | Verified |
| Commit | `144afc2f379b542fdd4e85a1fcd5e1f79112d95d` | Verified (HF API) |
| Total / active params | 30.5B total / ~3.3B activated | Verified (family naming + Instruct-2507 sibling card; Thinking card MoE structure) |
| Architecture | MoE transformer-decoder | Verified |
| Native context | 262,144 (1M optional path) | Verified |
| Reasoning | Dedicated Thinking-2507 (not hybrid switch) | Verified |
| License | Apache-2.0 | Verified |
| VRAM (sibling Qwen3-30B-A3B BF16 Transformers) | ~58,462 MB | Verified for non-2507 sibling table; treat 2507 as similar class (**Estimate** for exact 2507) |
| Why separate role | Materially different checkpoint vs hybrid dense 32B; stronger long-context + thinking specialization | Assumption |

### 4) Qwen3-4B — considered, not selected as named role

| Attribute | Value | Evidence class |
| --- | --- | --- |
| Parameters | 4.0B | Verified |
| VRAM BF16 short ctx | ~7,973 MB | Verified |
| Why not selected | Overlaps Qwen3-8B role; 8B closer to primary family quality for smoke tests | Assumption |

### 5) Qwen3-14B — considered, not selected

Useful mid-size dense hybrid. Rejected as neither the strongest practical baseline nor the cheapest CI target.

### 6) Qwen3-30B-A3B-Instruct-2507 — considered, not selected for first baseline

Strong non-thinking MoE with 256K context. Rejected as **primary** because hybrid dense Qwen3-32B covers both thinking and non-thinking without MoE complexity. May be revisited in comparative evaluation.

### 7) Qwen3-235B-A22B (-Instruct/-Thinking-2507) — rejected for Phase 2A hardware practicality

Flagship MoE; official SGLang BF16 uses multi-GPU TP (**verified**). Impractical as first local CobraBench baseline.

### 8) Qwen2.5-Coder-32B-Instruct — deferred coding challenger

| Attribute | Value | Evidence class |
| --- | --- | --- |
| Commit | `381fc969f78efac66bc87ff7ddeadb7e73c218a7` | Verified |
| License | Apache-2.0 | Verified |
| Why deferred | Materially code-specialized but prior generation; Qwen3 primary already claims coding gains. Separate coding challenger not required for initial baseline. | Assumption |

### 9) Qwen2.5-72B-Instruct — rejected for license + size

Hub license tag `other` / Qwen license (**verified**) plus large dense footprint make it a poor first Cobra Core intake versus Apache-2.0 Qwen3-32B.

---

## Intake suitability scores (0–5, estimates only)

Weights: Investigation 20%, Evidence grounding 15%, Hallucination resistance 15%, Citation 10%, Long-context 10%, Coding 10%, Local deployment 10%, Fine-tuning 5%, License/commercial 5%.

| Candidate | Inv 20% | Ground 15% | Hallu 15% | Cite 10% | Long 10% | Code 10% | Local 10% | FT 5% | Lic 5% | Weighted |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Qwen3-32B | 4.5 | 3.5 | 3.0 | 3.0 | 4.0 | 4.5 | 3.0 | 4.0 | 5.0 | **3.78** |
| Qwen3-8B | 3.5 | 3.0 | 2.5 | 2.5 | 3.5 | 3.5 | 4.5 | 4.5 | 5.0 | **3.45** |
| Qwen3-30B-A3B-Thinking-2507 | 4.5 | 3.5 | 3.0 | 3.0 | 5.0 | 4.0 | 2.5 | 3.0 | 5.0 | **3.70** |
| Qwen3-4B | 3.0 | 2.5 | 2.0 | 2.0 | 3.5 | 3.0 | 5.0 | 5.0 | 5.0 | **3.18** |
| Qwen2.5-Coder-32B-Instruct | 3.0 | 2.5 | 2.5 | 2.5 | 3.0 | 5.0 | 3.0 | 4.0 | 5.0 | **3.23** |
| Qwen2.5-72B-Instruct | 4.0 | 3.5 | 3.0 | 3.0 | 4.0 | 4.0 | 1.5 | 2.5 | 2.0 | **3.20** |

### Score rationales (condensed)

- **Investigation / coding:** Qwen3 official claims emphasize reasoning, coding, agents (**verified claims**; Cobra capability still **Unknown** until CobraBench).  
- **Grounding / hallucination / citation:** No CobraBench evidence yet — mid scores on purpose (**Assumption**).  
- **Long-context:** Thinking-2507 native 256K scores highest; dense 32B/8B native 32K + YaRN 128K.  
- **Local deployment:** Official Transformers memory tables favor 8B/4B; 32B BF16 needs ~63GB-class GPU memory.  
- **Fine-tuning:** Dense preferred over MoE for early LoRA (**Assumption**).  
- **License:** Apache-2.0 Qwen3 = 5; Qwen2.5-72B proprietary-tagged license = 2.

---

## Role recommendations

| Role | Recommendation | Justification |
| --- | --- | --- |
| Primary baseline | **Qwen3-32B** | Strongest practical dense hybrid for full CobraBench; Apache-2.0; pinable Hub commit |
| Resource-constrained | **Qwen3-8B** | Same family, official ~16GB BF16 footprint, CI/regression practicality |
| Reasoning challenger | **Qwen3-30B-A3B-Thinking-2507** | Distinct Thinking-2507 MoE + 256K; acquire **after** primary |
| Coding challenger | **None for Phase 2A** | Not forced; revisit Qwen2.5-Coder only if coding category underperforms |

---

## Unknowns / revisit triggers

- Actual CobraBench grounding, citation, and hallucination scores  
- Whether thinking mode helps or harms citation discipline  
- Exact disk bytes for Hub shards (API did not return sizes in this environment)  
- Whether YaRN 128K or 256K MoE is required for long-document cases  
- Future Qwen3.x releases superseding these pins  

Revisit if: a newer Apache-2.0 Qwen dense ≥32B appears; hardware cannot host 32B BF16/AWQ; or baseline reveals coding-specific failure warranting Qwen2.5-Coder.
