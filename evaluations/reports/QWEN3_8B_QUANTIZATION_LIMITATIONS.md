# Qwen3-8B Quantization Limitations (Phase 2E)

**Date:** 2026-07-22  
**Scope:** Document comparison limits. No new artifact acquired.

## Exact configuration used (baseline + diagnostics)

| Field | Value |
| --- | --- |
| Acquired artifact | Official BF16 safetensors (`Qwen/Qwen3-8B` @ `b968826d…`) |
| Load-time quantization | bitsandbytes 4-bit |
| Quant type | NF4 |
| Double quant | enabled |
| Compute dtype | float16 |
| Framework | Transformers |
| device_map | `auto` |
| max_memory | `{0: "9GiB", "cpu": "18GiB"}` |
| offload_folder | present under model revision tree |
| trust_remote_code | false |

## Official versus derived

- **Official identity:** BF16 checkpoint (acquired).  
- **Derived at load time:** 4-bit weights via bitsandbytes (not a separately downloaded AWQ/GPTQ artifact).

## Known comparison limits

- Results are **not** native BF16 quality claims.  
- No same-session 8-bit or BF16 comparison was run in Phase 2E.  
- Therefore **quantization causal impact on each weakness is Unknown (U)** unless a diagnostic isolates another variable.

## What would be required for precision comparison

1. Hardware capable of native BF16 or 8-bit without crash (more VRAM/RAM).  
2. Separate locked cohort with identical prompts/seeds.  
3. Explicit protocol version distinguishing precision cohorts.

## Phase 2E stance

Do not attribute long-document early stopping (~128 tokens) or contradiction depth solely to 4-bit without a precision A/B. Mark R (runtime/quantization) as **possible contributing**, not primary, unless evidence appears.
