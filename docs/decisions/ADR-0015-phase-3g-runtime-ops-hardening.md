# ADR-0015 — Phase 3G Priority 1 runtime ops hardening

## Status

Accepted — Priority 1 implemented as tooling/docs/pins only.

## Context

Phase 3F qualified Qwen3-8B on RunPod Linux (`phase-3f-qualified`). Phase 3G Priority 1 improves operational reliability, reproducibility, and cost guidance without changing model or inference behavior.

## Decision

1. Keep Phase 3F inference pins identical (torch `2.6.0+cu124`, transformers `5.14.1`, bitsandbytes `0.49.2`, etc.).
2. Split runtime vs development requirements.
3. Pin container image tag + Docker Hub digests used in Phase 3F.
4. Add SSH bootstrap, provision preflight, cleanup verify, and env verify scripts.
5. Document VRAM envelope (~6 GiB peak) and lowest-cost supported GPU recommendations.
6. Do **not** run CobraBench, train, deploy, or alter score **0.840**.

## Consequences

* Operators can reproduce the qualified environment with fewer manual steps.
* New GPU SKUs remain recommendations until abbreviated smoke is run.
* Runtime requalification is **not** required for P1 acceptance.

## Required statement

> Phase 3G Priority 1 hardens cloud operations around the Phase 3F qualified runtime. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, modify prompts or model weights, authorize training, or deploy an inference service.
