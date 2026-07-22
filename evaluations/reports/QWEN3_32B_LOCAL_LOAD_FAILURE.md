# Qwen3-32B Local Load Failure Evidence (Phase 2C)

**Date:** 2026-07-22  
**Environment key:** `local-windows-rtx4070-12gb`  
**Status:** Artifact acquisition and SHA256 verification succeeded. Local inference validation failed.  
**Not a model-defect claim.** Not Cobra Core.

## Supported conclusion

> The selected Qwen3-32B runtime configuration is not dependable on the current 12 GB VRAM / approximately 32 GB RAM Windows machine.

## Model identity (unchanged)

| Field | Value |
| --- | --- |
| Repository | `Qwen/Qwen3-32B` |
| Pinned revision | `9216db5781bf21249d130ec9da846c4624c16137` |
| Artifact count | 27 |
| Total bytes | 65,540,298,478 |
| Acquisition | Locally SHA256 verified |
| Official precision of acquired artifacts | BF16 safetensors |

## Why the chosen path was reasonable

1. Preserve official pinned BF16 identity (ADR-0001).  
2. Match Phase 2B Qwen3-8B practice: load-time bitsandbytes 4-bit on official BF16 (not a silent third-party GGUF).  
3. Official AWQ-INT4 still reports ~19 GB Transformers footprint — exceeds 12 GB VRAM without offload.  
4. Disk free (~633 GB) was sufficient for acquisition.

## Attempts

### Attempt 1

| Field | Value |
| --- | --- |
| Timestamp window | 2026-07-22 ~19:30–19:38 UTC |
| Command | `scripts/validate_model_load.py --manifest model-cards/qwen/qwen3-32b.manifest.json` |
| Framework | Transformers + bitsandbytes |
| Precision | `load_in_4bit=True`, NF4, double quant, compute dtype float16 |
| Device map | `auto` |
| max_memory | `{0: "9GiB", "cpu": "18GiB"}` |
| Free RAM at start | ~10.8 GB |
| GPU free | ~10941 MiB |
| Result | Process crash Windows exit `0xC0000005` (ACCESS_VIOLATION) |
| Progress | Weight load ~16% (~112/707 modules) |

### Attempt 2

| Field | Value |
| --- | --- |
| Timestamp window | 2026-07-22 ~19:39–19:45 UTC |
| Settings | Same 4-bit path; `max_memory={0:"8GiB","cpu":"12GiB"}`; `offload_folder` + `offload_state_dict=True` |
| Free RAM at start | ~13.7 GB |
| Result | Same crash `0xC0000005` |
| Progress | Weight load ~13% (~90/707 modules) |

No successful tokenizer confirmation, chat-template check, `COBRA_MODEL_OK` response, or grounded inference was obtained.

## Ruled out / not claimed

- Not claimed: upstream weights are corrupt (hashes verified).  
- Not claimed: Qwen3-32B is globally unusable.  
- Not attempted (by design): third-party GGUF; Thinking-2507; silent AWQ identity swap; further retries after two crashes.

## Remains uncertain

- Whether a ≥24 GB VRAM host can run official AWQ stably.  
- Whether ≥64 GB system RAM would make hybrid 4-bit of official BF16 stable on Windows.  
- Exact native fault inside the crash (no secret-bearing stack dump preserved).

## Why further local retries are not justified

Repeated ACCESS_VIOLATION during early weight load under low free RAM indicates systemic resource pressure / instability, not a flaky one-off. Additional attempts risk system instability without changing the hardware envelope.

## What could permit future evaluation

1. Host with ≥24 GB VRAM + official `Qwen/Qwen3-32B-AWQ` as a **separate** pinned identity.  
2. Host with ≥64 GB RAM for hybrid offload of official BF16.  
3. Cloud A100/H100 cohort for BF16 or documented quant.

## Separation of states

| Layer | Qwen3-32B on this environment |
| --- | --- |
| Acquisition / hash verification | Succeeded |
| Runtime validation | Failed / unsupported on environment |
| Benchmark eligibility | Blocked by runtime |
| CobraBench scores | None |

See also: `docs/QWEN3_32B_RUNTIME_DECISION.md`, `docs/decisions/ADR-0002-qwen3-baseline-results.md`.
