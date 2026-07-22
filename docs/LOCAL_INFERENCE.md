# Local Inference

## Runtime choice (this machine class)

For RTX 4070 12GB:

- Official Qwen3-8B BF16 does **not** fit fully on GPU (~16GB class).
- Selected approach: **Transformers** loading the **official pinned BF16 artifacts** with **bitsandbytes 4-bit** at load time (fallback: float16 GPU/CPU offload).
- This is not a third-party weight download.

## Interface

- Provider-neutral engine: `cobra_core.inference.engine.LocalInferenceEngine`
- Qwen adapter: `cobra_core.providers.qwen_local.QwenLocalAdapter`
- `trust_remote_code=False` by default

## Smoke tests

```bash
python scripts/run_smoke_tests.py
```

Artifacts:

```text
evaluations/results/smoke/<run-id>/
  run.json
  prompt.json
  response.txt
  metrics.json
  environment-reference.json
```

These are technical smoke tests, not CobraBench scores.

## Safety

- Max new tokens capped
- Context overflow checks
- Quarantined / non-acquired models refused
- CUDA OOM unloads model and surfaces error
- Secrets redacted from persisted metadata helpers
