# Qwen3-8B Output-Cap Diagnostic (Cohort A)

**Status:** Deferred — blocked before generation (`0xC0000005` during load; not a model-quality test failure).  
**Planned run ID:** `20260722T220000Z-2ediag01`  
**Official CobraBench:** No — do not mix into 0.840.

## Baseline static facts (not new generations)

| Case | Baseline max_new_tokens | output_tokens | finish_reason | Cap-limited? |
| --- | ---: | ---: | --- | --- |
| cb-023-long-memo-key-facts | 512 | 127 | completed | **No** |
| cb-024-long-policy-exceptions | 512 | 128 | completed | **No** |
| cb-001-evidence-grounded-investigation | 512 | 512 | completed | **Likely yes** |

## Planned comparison

Hold temp=0, seed=123, thinking off. Caps: 1024 and 2048 (plus baseline 512 reference).

## Interim conclusion

Long-document weakness **cannot** be attributed primarily to the 512-token cap from baseline evidence alone. Investigation verbosity on cb-001 remains a plausible Class 1 runtime issue pending measurement.
