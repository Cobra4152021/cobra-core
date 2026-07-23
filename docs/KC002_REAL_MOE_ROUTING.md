# KC-002 — Real MoE Routing

## Status

**NOT EXECUTED** on real GPT-OSS weights.

## Intent

Instrument real router logits / top-k experts for:

1. text-only  
2. correct image + prompt  
3. wrong image + prompt  
4. blank image  
5. noise image  

Router remains **frozen** unless measurements show adaptation is required (KC-001 community hypothesis: projector-only fails; QLoRA on attention is the first remedy).

## Command (CUDA host)

```bash
cd kc002 && make moe
```

## Surrogate reference

KC-001 measured routing on Tiny MoE only — superseded for decision-making once this doc is filled with real-weight tables.
