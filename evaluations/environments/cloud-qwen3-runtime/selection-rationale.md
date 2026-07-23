# Dependency selection rationale (proposed)

| Package | Version | Why |
| --- | --- | --- |
| Python | 3.11 (pref) / 3.12 | Stable scientific wheels; avoid 3.13 after Windows instability |
| torch | 2.6.0+cu124 | Matches validated micro-op stack; official Linux wheel |
| transformers | 5.14.1 | Qwen3 support; pinned for reproducibility |
| accelerate | 1.14.0 | Explicit device_map support |
| bitsandbytes | 0.49.2 | 4-bit NF4 path used in prior phases |
| numpy | 2.2.6 | Has cp311/cp312 wheels; conservative |
| safetensors / tokenizers / huggingface-hub | pinned | Load path integrity |
| psutil / pytest | pinned | Telemetry and tests |

No FlashAttention, xFormers, DeepSpeed, vLLM, or source builds in Phase 3F first qualification.
