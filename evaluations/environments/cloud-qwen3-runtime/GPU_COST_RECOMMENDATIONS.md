# Lowest-cost supported GPU recommendations (Phase 3G P1)

**Baseline:** Phase 3F Outcome A on NVIDIA A40 @ **$0.44/hr** (RunPod Community Cloud).  
**VRAM need:** ~6 GiB peak under qualified 4-bit path → **≥16 GB** required by policy.

## Recommendation matrix

Rates are **indicative** from Phase 3F authorization records / public RunPod pricing checks.  
**Always re-verify the live displayed hourly price before launch.** Refuse if above authorized caps.

| Priority | GPU class | Min VRAM | Why supported | Indicative Community $/hr | Est. savings vs A40 $0.44/hr | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 (prefer create) | **NVIDIA L4** | 24 GB | Authorized primary SKU; fits envelope | ~$0.39–$0.44 | ~0–11% | Prefer US on-demand; was original Phase 3F primary |
| 2 (fallback create) | **NVIDIA RTX A5000** | 24 GB | Authorized fallback ≤ $0.35/hr | ~$0.16–$0.35 | **~20–64%** | Use only if L4 unavailable; confirm RAM≥32 GB |
| 3 (adopt only) | **NVIDIA A40** | 48 GB | Phase 3F qualified host | $0.44 (measured) | baseline | Acceptable if already running; do not prefer for new create |
| Avoid (unless re-auth) | Spot / interruptible | — | Not in current authorization | — | — | Forbidden without new auth |
| Avoid (P1) | Multi-GPU / endpoints | — | Out of scope | — | — | Deployment forbidden |

## Session cost heuristics

| Scenario | GPU $/hr | 1.0 h useful work + 0.75 h setup | 1.0 h work + 0.25 h setup (P1 target) |
| --- | --- | --- | --- |
| A40 (3F) | $0.44 | ~$0.77 | ~$0.55 |
| L4 @ $0.44 | $0.44 | ~$0.77 | ~$0.55 |
| A5000 @ $0.25 | $0.25 | ~$0.44 | ~$0.31 |

**Estimated cloud savings from P1 ops (no SKU change):**  
Cutting avoidable setup/SSH recovery from ~45 min → ~15 min on a $0.44/hr pod ≈ **$0.22/session**.

**Estimated cloud savings from SKU right-sizing (after abbreviated smoke):**  
A5000 at $0.25/hr vs A40 $0.44/hr ≈ **~$0.19/hr** (~43%) while idle or working.

## Support rules

1. One active GPU instance max.  
2. On-demand only.  
3. No public Jupyter / inference endpoint.  
4. Model + venv on `/workspace` (or network volume), not overlay `/`.  
5. After any new SKU: run abbreviated smoke (1 load + 1 generate + 1 qual) before treating it as supported.
