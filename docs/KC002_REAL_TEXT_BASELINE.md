# KC-002 — Real GPT-OSS Text Baseline

## Status

**NOT EXECUTED** — blocked by environment gate (CPU-only PyTorch, 12GB VRAM, ~8.5GB free disk).

## Plan (run on ≥24GB CUDA host)

```bash
cd kc002 && make validate-env && make text-baseline
```

Artifact: `artifacts/experiments/real_text_baseline.json`

## Prompts (preserved from KC-001)

| ID | Prompt |
|----|--------|
| T1 | Say the word "ok" and nothing else. |
| T2 | What is 17+4? Reply with only the number. |
| T3 | Translate to French: good morning |
| T4 | Write a JSON object with keys a=1 and b=2 only. |
| T5 | List three primary colors as a comma-separated list. |

## Required per-prompt fields

prompt ID, output, input/output tokens, latency, peak VRAM, repeat_match (seed=42), finish reason.

## Gate

Do not proceed to vision training if outputs are unstable or clearly malformed.
