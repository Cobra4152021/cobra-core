# ADR-0002 — Qwen3 Baseline Results (Phase 2C)

- **Status:** Accepted (hard-stop; incomplete dual-model baseline)
- **Date:** 2026-07-22
- **Phase:** 2C — Qwen3-32B acquisition and first CobraBench baseline

## Context

Phase 2B verified local acquisition and inference for **Qwen3-8B** (development baseline) on this machine (RTX 4070 12 GB, ~32 GB system RAM). Phase 2C authorized acquisition of the pinned **Qwen3-32B** primary baseline and a dual-model CobraBench v0.1 evaluation against Qwen3-8B under identical protocol.

## Models evaluated

| Role | Model | Revision | Acquisition | Load validation | CobraBench v0.1 |
| --- | --- | --- | --- | --- | --- |
| Development control | Qwen3-8B | `b968826d9c46dd6066d109eabc6255188de91218` | Verified | Previously passed (Phase 2B) | **Not run** (Gate 5 stop) |
| Primary baseline | Qwen3-32B | `9216db5781bf21249d130ec9da846c4624c16137` | Verified | **Failed** (process crash) | **Not run** |

## Benchmark version

**CobraBench v0.1** frozen under `benchmarks/releases/cobrabench-v0.1/` (28 synthetic cases). Inventory hashes recorded. Cases were not altered after freeze intent.

## Evaluation protocol (planned, not executed)

- Identical cases, system/user prompts, evidence, `max_new_tokens=512`
- Thinking **disabled** for both
- `temperature=0`, `seed=123`
- Separate objective / rule / human / advisory judge layers
- Load-time bitsandbytes 4-bit on official BF16 artifacts (Phase 2B-comparable protocol)

## Results by category

**Not available.** Dual-model CobraBench did not start because Gate 5 failed.

## Reliability findings

- Qwen3-32B artifacts: 27 files, 65,540,298,478 bytes; local SHA256 inventory complete; manifest `acquired`.
- Qwen3-32B load attempts (bnb 4-bit + GPU/CPU and disk offload) crashed Windows process with exit `0xC0000005` during weight loading (~13–16%).
- Available system RAM (~11–14 GB free of ~32 GB total) is insufficient for safe hybrid load of 32B 4-bit on this host.

## Resource findings

| Resource | Value |
| --- | --- |
| GPU | RTX 4070 12 GB |
| Official BF16 GPU footprint | ~61 GB (Qwen Transformers benchmark) — not feasible |
| Official AWQ-INT4 footprint | ~19 GB — exceeds 12 GB without offload |
| Disk free at acquisition | ~633 GB — sufficient |
| System RAM | ~32 GB total — insufficient headroom for stable 32B hybrid load |

## Decision

**Stop local Qwen3-32B evaluation due to resource impracticality / load instability on the current machine.**

Do **not** designate either model as Cobra Core.

Do **not** begin fine-tuning, LoRA, or weakness-targeted dataset design without separate authorization.

### Authorized next steps (pick explicitly)

1. Re-run Gate 5–10 on hardware with ≥24 GB VRAM (prefer official AWQ as a separate pinned identity) or ≥64 GB RAM for hybrid BF16+4-bit.  
2. Authorize an **8B-only** CobraBench v0.1 control baseline on the current machine.  
3. Authorize a cloud cohort for comparable 32B runs.

## Risks

- Acquired 32B weights occupy ~65 GB on D: without producing baseline scores.  
- Future “comparable” runs must match precision/offload class or be labeled a separate cohort.  
- Premature publication of CobraBench prompts risks contamination (see contamination policy).

## Unknowns

- Whether a third-party GGUF would load here (intentionally not attempted; unapproved derivative).  
- Whether official AWQ with extreme offload would avoid `0xC0000005` on 12 GB (not attempted as primary identity).

## Benchmark limitations

- v0.1 is small (28 cases), synthetic, and heuristic auto-scorers are not ground truth.  
- Without dual-model outputs, category comparisons remain unavailable.

## Revisit conditions

Revisit when at least one of:

- Load validation for the selected 32B format passes twice consecutively, or  
- A separately approved hardware/runtime cohort is available, or  
- An 8B-only interim baseline is explicitly authorized.

## Next authorized phase

**None automatically.** Await explicit authorization for hardware-upgrade re-run, 8B-only CobraBench, or alternate cohort.

---

> Neither Qwen3-8B nor Qwen3-32B is designated Cobra Core by this baseline evaluation.
