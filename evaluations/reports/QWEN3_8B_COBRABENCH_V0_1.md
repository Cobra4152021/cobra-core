# Qwen3-8B — CobraBench v0.1 Report

**Status:** Not executed — stopped after Gate 5 failure on Qwen3-32B.  
**Date:** 2026-07-22  
**Not Cobra Core.**

## Model reference

| Field | Value |
| --- | --- |
| Source | `https://huggingface.co/Qwen/Qwen3-8B` |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Acquisition | Verified (Phase 2B; revalidated Phase 2C) |
| Prior smoke | Six technical smoke tests passed (Phase 2B) |
| Runtime / precision | Transformers + bitsandbytes 4-bit from official BF16 |
| Hardware | RTX 4070 12 GB |
| CobraBench version | v0.1 frozen and ready; **suite not run** |

## Why this report is empty of scores

Phase 2C execution gates require stopping at the first failed gate. Gate 5 (Qwen3-32B load validation) failed; therefore Gate 7 (Qwen3-8B CobraBench) was not started in this phase.

An **8B-only** CobraBench v0.1 control baseline remains a recommended interim step and requires separate authorization (see ADR-0002).

## Category-level scores

**Not computed.**

## Objective / rule / human / judge

**Not run.**

## Citation / hallucination / contradiction / refusal

**Not measured.**

## Latency / throughput

Only Phase 2B smoke indicative rates are available (~0.8–7 tok/s under 4-bit). Not a CobraBench result.

## Failures / limitations

- No CobraBench outputs for this phase.  
- Do not treat Phase 2B smoke as category quality evidence.
