# GPU Compatibility Matrix — Qwen3-8B cloud Linux (4-bit NF4)

**Qualified path:** Phase 3F Outcome A — bitsandbytes 4-bit NF4, double quant, float16, `device_map={"": 0}`  
**Measured peak VRAM:** ~5.88–6.32 GiB on NVIDIA A40  
**Policy minimum VRAM to attempt:** 16 GB  
**Costs:** Indicative Community Cloud-style $/hr; **re-verify live price before launch.**  
**Qualification status meanings:** `qualified` | `supported-candidate` | `likely` | `oversized` | `untested`

Smoke-test requirement: if status ≠ `qualified`, run at least load + generate + 1 qual before treating SKU as supported.

| GPU | VRAM | Expected compatibility | Expected runtime (vs A40) | Expected cloud cost (indicative) | Qualification status | Smoke-test requirement |
| --- | ---: | --- | --- | --- | --- | --- |
| **RTX A5000** | 24 GB | Fits envelope with headroom | Similar load/gen; I/O bound more than compute for smoke | ~$0.16–$0.35/hr (prefer ≤$0.35 auth fallback) | `supported-candidate` | **Required** before support claim |
| **RTX 3090** | 24 GB | Fits envelope; consumer/workstation class may appear on some clouds | Similar; watch host RAM ≥32 GB and driver | Highly variable (~$0.20–$0.45/hr) | `likely` | **Required**; confirm bitsandbytes/CUDA stack |
| **RTX 4090** | 24 GB | Fits envelope; strong consumer GPU | Similar or slightly faster gen; load still disk-bound | Often mid (~$0.30–$0.55/hr) | `likely` | **Required**; confirm template CUDA ≥12.x |
| **L4** | 24 GB | Authorized primary create SKU; fits envelope | Similar to A40 for this workload | ~$0.39–$0.44/hr | `supported-candidate` | **Required** (preferred create path; not yet smoke-qualified in-repo) |
| **A10G** | 24 GB | Fits envelope; common cloud T4-successor class | Similar | ~$0.40–$0.75/hr depending on provider | `likely` | **Required** |
| **A40** | 48 GB | **Proven** in Phase 3F | Cold load ~75 s; warm ~22–25 s; gen ~1.4–9.3 s | **$0.44/hr** measured | **`qualified`** | Not required to re-run for docs; re-run only if stack/image changes |
| **A100** (40/80 GB) | 40–80 GB | Compatible; oversized vs ~6 GiB need | Similar functional; little quality benefit for 4-bit 8B smoke | Typically **higher** ($1+/hr class) — avoid for cost | `oversized` | Optional abbreviated smoke if used; **not recommended** for cost |
| **H100** | 80 GB | Compatible; heavily oversized | Similar functional; poor $/smoke | Typically **much higher** — avoid | `oversized` | Optional only under special auth; **not recommended** |

## Notes

1. **Compatibility** here means “can host the locked 4-bit path,” not “matches A40 latency bit-for-bit.”
2. System RAM policy: **≥32 GB** (Phase 3F pod had 50 GB).
3. Disk: model + venv on persistent `/workspace` (or equivalent); overlay-only hosts fail.
4. Multi-GPU is out of scope; use single GPU 0.
5. Spot/interruptible instances require separate authorization.
6. Changing quant to fit &lt;16 GB is **out of scope** and needs a new qualification program.

## Recommendation (cost)

1. **Create:** L4  
2. **Fallback create:** A5000 ≤ authorized $/hr  
3. **Adopt:** A40 if already running  
4. **Avoid for routine ops:** A100/H100 unless latency experiments are explicitly funded
