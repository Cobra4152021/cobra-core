# Qwen3-8B Thinking-Mode Diagnostic

**Status:** Deferred — blocked before generation (environment), not a failed model-quality test.  
**Planned run ID:** `20260722T220000Z-2ediag01` (cohort B) — do not reuse for a later successful run.  
**Baseline comparison:** thinking **disabled** in `20260722T200000Z-8bba5e01`

## Planned design

Hold temperature=0, seed=123, max_new_tokens=512. Cases: cb-019, cb-004, cb-018, cb-015 (control). Compare enable_thinking true vs false.

## Observed (baseline only)

- Official v0.1 interim cohort used thinking disabled.  
- No thinking-enabled final-answer metrics available yet.

## Blocker

Process crash `0xC0000005` while loading weights under GPU/RAM contention. Generations completed: **0**.

## Interim conclusion

Thinking-mode effect remains **Unknown**. Do not fabricate deltas. Do not mix into the official 0.840 score.
