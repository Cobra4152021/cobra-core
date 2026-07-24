# Validated VRAM envelope (Phase 3F → Phase 3G)

**Baseline:** tag `phase-3f-qualified` (`0a2af49ee86451c374a600579d3644c811cd12c0`)

## Qualified configuration (unchanged)

| Setting | Value |
| --- | --- |
| Model | Qwen3-8B |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Inventory hash | `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f` |
| Quantization | bitsandbytes 4-bit NF4, double quant, float16 compute |
| Device map | `{"": 0}` (explicit GPU 0; no CPU/disk offload) |
| Peak VRAM (measured) | **6,318,342,144 bytes (~5.88 GiB)** |
| Peak VRAM (load-only) | **6,173,550,592 bytes (~5.75 GiB)** |
| Qualified GPU | NVIDIA A40 48 GB (oversized vs need) |

## Production envelope (documentation only)

| Envelope | Value | Rationale |
| --- | --- | --- |
| Minimum VRAM to attempt | **16 GB** | Phase 3F authorization + safety margin above ~6 GiB peak |
| Recommended VRAM | **24 GB** | Headroom for longer contexts / fragmentation |
| Comfortable / qualified class | **40–48 GB** | What Phase 3F actually ran (A40) |

## Non-goals

* This document does **not** authorize tighter quantization or offload.
* Changing quantization/device_map requires a new qualification (not Phase 3G P1).
