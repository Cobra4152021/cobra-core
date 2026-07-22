# Qwen3-8B CobraBench v0.1 Protocol (Interim)

**Date:** 2026-07-22  
**Protocol file:** `evaluations/protocols/qwen3-8b-cobrabench-v0.1.json`  
**Status:** Frozen for the Phase 2D interim baseline run.

## Purpose

Establish the first complete CobraBench v0.1 execution, scoring, review, and reporting workflow using **Qwen3-8B only**.

This is **not** a comparison against Qwen3-32B.  
Qwen3-8B is **not** designated Cobra Core.

## Thinking-mode decision

**Primary cohort: thinking disabled** (`enable_thinking=False`).

Reasons:

- lower runtime cost on the local RTX 4070 host,
- cleaner answer-format evaluation,
- easier reproducibility,
- fewer reasoning-content parsing differences,
- establishes the ordinary instruct baseline first.

Thinking-enabled vs disabled may be studied later as a **separate cohort**. Do not mix modes in one score.

## Inference settings (primary)

| Setting | Value |
| --- | --- |
| Temperature | `0.0` |
| Seed | `123` |
| max_new_tokens | `512` (identical across cases) |
| top_p | `1.0` |
| Thinking | disabled |
| Precision | bitsandbytes 4-bit NF4 on official BF16 artifacts |
| device_map | `auto` with `max_memory={0:"9GiB","cpu":"18GiB"}` |
| Retries | none (preserve failures) |

## Benchmark pin

- Release: `cobrabench-v0.1`
- Inventory SHA256: `372edd36808909e191a4a6e2b8d012373f3b4a3f1e3831488b866ff6c598bf5a`
- Release tree SHA256: `ee4fcd14840d580da8676540a5b03fcf624e5bde90990283d2e000980602a0ee`

Do not alter frozen v0.1 cases after execution begins.
