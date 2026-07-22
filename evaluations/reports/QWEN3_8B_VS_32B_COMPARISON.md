# Qwen3-8B vs Qwen3-32B — Comparison Status

**Date:** 2026-07-22  
**Status:** No dual-model comparison exists.

## Explicit non-results

- Qwen3-32B completed artifact acquisition and SHA256 verification.
- Qwen3-32B **did not** complete load validation on this machine (crash `0xC0000005`).
- **No Qwen3-32B CobraBench scores exist.**
- Qwen3-8B interim CobraBench v0.1 results **must not** be used to infer Qwen3-32B performance.
- Future comparison requires a compatible environment and a completed 32B load gate under a frozen protocol.

## What was completed instead

An authorized **Qwen3-8B-only** interim baseline under CobraBench v0.1. See:

- `evaluations/reports/QWEN3_8B_COBRABENCH_V0_1.md`
- `evaluations/reports/QWEN3_32B_LOCAL_LOAD_FAILURE.md`
- `docs/decisions/ADR-0003-qwen3-8b-interim-baseline.md`

## Forbidden interpretations

Do not treat 8B category scores as evidence that 32B would be better, worse, or similar.
