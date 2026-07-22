# Qwen3-32B Runtime Decision (Phase 2C)

**Date:** 2026-07-22  
**Status:** Conditional acquisition authorized; load validation is a separate hard gate.  
**Does not designate Cobra Core.**

## Labels

| Label | Meaning |
| --- | --- |
| **Official fact** | From Qwen / Hugging Face docs or model card |
| **Local measurement** | Observed on this machine |
| **Calculated estimate** | Derived from known sizes / formulas |
| **Engineering assumption** | Judgment used to proceed or stop |

---

## Official source identity

| Field | Value | Label |
| --- | --- | --- |
| Source model | `Qwen/Qwen3-32B` | Official fact |
| Source URL | `https://huggingface.co/Qwen/Qwen3-32B` | Official fact |
| Pinned revision | `9216db5781bf21249d130ec9da846c4624c16137` | Official fact (Phase 2A pin) |
| License | Apache-2.0 | Official fact |
| Native precision artifact | BF16 safetensors shards | Official fact |

No third-party derivative is selected as the acquired identity.

---

## Local hardware / storage (this machine)

| Field | Value | Label |
| --- | --- | --- |
| GPU | NVIDIA GeForce RTX 4070 | Local measurement |
| VRAM | 12282 MiB (~12 GB) | Local measurement |
| CUDA | Available (torch `2.6.0+cu124`) | Local measurement |
| System RAM total | ~31.9 GB | Local measurement |
| System RAM free (pre-acq) | ~9.4 GB | Local measurement |
| D: free | ~633 GB | Local measurement |
| Current model-cache use | ~16.4 GB (Qwen3-8B only) | Local measurement |
| bitsandbytes | Available | Local measurement |
| accelerate | Available | Local measurement |

---

## Path evaluation (required order)

### 1) Official BF16 checkpoint with GPU execution

| Item | Value | Label |
| --- | --- | --- |
| Official Transformers BF16 short-context footprint | ~62751 MB (~61 GB) | Official fact (Qwen speed benchmark) |
| Fits 12 GB VRAM? | **No** | Calculated estimate |
| Decision | **Rejected for GPU-resident execution** | Engineering assumption |

### 2) Official BF16 checkpoint with CPU / hybrid offload

| Item | Value | Label |
| --- | --- | --- |
| On-disk size | ~65–70 GB expected | Calculated estimate |
| Storage gate (need ~70 + 8 temp + 20 margin ≈ 98 GB) | Pass (~633 GB free) | Local measurement + calculated |
| Runtime | Transformers + `device_map="auto"` + bitsandbytes 4-bit load of official BF16 | Engineering assumption (matches Phase 2B 8B path) |
| Expected weight memory (4-bit) | ~16–20 GB resident + activations/KV | Calculated estimate |
| GPU budget | Cap ~9 GiB on GPU; remainder CPU/RAM | Engineering assumption |
| Risk | Total RAM ~32 GB leaves little headroom; paging/OOM possible under load | Local measurement + engineering assumption |
| Decision | **Selected for acquisition and load-attempt** | Engineering assumption |

### 3) Official quantized Qwen artifact (`Qwen/Qwen3-32B-AWQ`)

| Item | Value | Label |
| --- | --- | --- |
| Exists as official Qwen repo | Yes | Official fact |
| Transformers AWQ-INT4 short-context VRAM | ~19109 MB (~19 GB) | Official fact (Qwen speed benchmark) |
| Fits 12 GB without offload? | **No** | Calculated estimate |
| Identity change | Would be a **separate** acquired artifact (must not overwrite BF16 identity) | Engineering assumption |
| Decision | **Not selected** for primary baseline identity; remain available as future alternative if BF16 hybrid load fails | Engineering assumption |

### 4) Pinned third-party / derivative quantization

| Decision | **Rejected** — not required while official BF16 + load-time 4-bit remains the Phase 2B-consistent path | Engineering assumption |

---

## Selected format and runtime

| Field | Selection | Label |
| --- | --- | --- |
| Acquired artifact | Official BF16 pinned revision | Decision |
| Inference precision | bitsandbytes 4-bit from official BF16 (not a separate download) | Decision |
| Runtime framework | Hugging Face Transformers | Decision |
| Offload configuration | `device_map="auto"`, `max_memory={0: "9GiB", "cpu": "18GiB"}` (conservative) | Engineering assumption |
| Context length for baseline testing | Short prompts only; target ≤2k tokens input; `max_new_tokens=512` | Engineering assumption |
| Thinking policy (primary baseline) | **Disabled for both 8B and 32B** (`enable_thinking=False`) | Decision |
| Temperature / seed | `temperature=0`, `seed=123` when supported | Decision |

---

## Expected resource use

| Resource | Estimate | Label |
| --- | --- | --- |
| Storage (final) | ~65–70 GB | Calculated estimate |
| Temporary download overhead | ~5–15 GB peak extras | Calculated estimate |
| Runtime memory | ~16–24 GB combined GPU+CPU working set | Calculated estimate |
| Evaluation runtime | Slow; hybrid offload may be <5 tok/s; full ~28-case suite may take many hours | Engineering assumption |

---

## Why this is acceptable for CobraBench v0.1

1. Preserves the **official pinned source identity** used in ADR-0001.  
2. Matches the Phase 2B development-baseline pattern (official BF16 + load-time 4-bit).  
3. Allows a same-protocol comparison against Qwen3-8B (identical cases, prompts, thinking off, temp 0).  
4. Avoids silently substituting a third-party GGUF/derivative as “Qwen3-32B”.

## Known differences from native BF16

- Load-time 4-bit quantization changes numerical behavior vs native BF16.  
- Hybrid CPU offload changes latency and may change generation dynamics vs single-GPU BF16.  
- Results are **not** a claim about datacenter BF16 Qwen3-32B quality.

## Comparison limitations vs Qwen3-8B

- Both use bitsandbytes 4-bit on official BF16 for fairness of *protocol*, but absolute quality vs native BF16 is unknown for both.  
- 32B will likely run far slower and with heavier offload than 8B.  
- Do not normalize away speed/resource differences in reports.

## Direct comparability to future runs

Comparable **only** when future runs use:

- same CobraBench version (`cobrabench-v0.1`),
- same model revision,
- same thinking policy,
- same load precision / offload class,
- same `max_new_tokens` / temperature / seed policy.

Native BF16 GPU runs on different hardware are a **separate cohort**.

---

## Hard-stop conditions (active)

Stop **before acquisition** if storage insufficient — **not triggered**.  
Stop **before CobraBench** if load validation fails, OOM, or uncontrolled paging — **TRIGGERED (Gate 5)**.

### Gate 5 load-validation evidence (2026-07-22)

| Attempt | Settings | Free RAM at start | Result | Label |
| --- | --- | --- | --- | --- |
| 1 | bnb 4-bit, `max_memory={0:9GiB,cpu:18GiB}` | ~10.8 GB | Windows process crash `0xC0000005` during weight load (~16%) | Local measurement |
| 2 | bnb 4-bit, `max_memory={0:8GiB,cpu:12GiB}`, disk `offload_folder` | ~13.7 GB | Same crash `0xC0000005` during weight load (~13%) | Local measurement |

No successful tokenizer/model inference was obtained for Qwen3-32B on this machine.  
CobraBench dual-model evaluation was **not started**.

## Feasibility decision

**CONDITIONAL PASS for Gate 2 (storage + acquisition).**  
**FAIL for Gate 5 (load validation).**  

### Most defensible alternatives (do not auto-proceed without authorization)

1. Host with ≥24 GB VRAM and evaluate official `Qwen/Qwen3-32B-AWQ` as a **separate** pinned identity.  
2. Host with ≥64 GB system RAM (or large pagefile + validated disk offload) for hybrid 4-bit of official BF16.  
3. Cloud A100/H100 cohort for native BF16 / comparable single-GPU runs.  
4. Run **Qwen3-8B-only** CobraBench v0.1 as an interim control baseline (separate authorization).
