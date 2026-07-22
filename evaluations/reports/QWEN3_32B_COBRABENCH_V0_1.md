# Qwen3-32B — CobraBench v0.1 Report

**Status:** Incomplete — Gate 5 load validation failed.  
**Date:** 2026-07-22  
**Not Cobra Core.**

## Model reference

| Field | Value |
| --- | --- |
| Source | `https://huggingface.co/Qwen/Qwen3-32B` |
| Revision | `9216db5781bf21249d130ec9da846c4624c16137` |
| Acquisition | Verified — 27 artifacts, 65,540,298,478 bytes |
| Runtime / precision (intended) | Transformers + bitsandbytes 4-bit from official BF16 |
| Hardware | RTX 4070 12 GB; ~32 GB system RAM |
| CobraBench version | v0.1 (frozen; 28 cases) |

## Load validation

Two attempts crashed the Python process with Windows exit code `0xC0000005` during weight loading (~13–16%). No tokenizer/chat-template confirmation, no `COBRA_MODEL_OK` response, no grounded-passage check, and no CobraBench case outputs were produced.

See `docs/QWEN3_32B_RUNTIME_DECISION.md` and `docs/decisions/ADR-0002-qwen3-baseline-results.md`.

## Category-level scores

**Not computed** — no model outputs.

## Objective / rule / human / judge

| Layer | Status |
| --- | --- |
| Objective metrics | Not run |
| Rule-based checks | Not run |
| Human review | Not run |
| LLM-as-judge | Not run |

## Citation / hallucination / contradiction / refusal

**Not measured.**

## Latency / throughput

**Not measured** (load did not complete).

## Failures

1. Gate 5 hard stop: unstable/impossible local load on current resources.  
2. Gates 7–10 (evaluation, human review, comparison scoring) not started.

## Limitations

Results must not be invented. Re-run only after a passing load gate on suitable hardware or an authorized alternate runtime identity.
