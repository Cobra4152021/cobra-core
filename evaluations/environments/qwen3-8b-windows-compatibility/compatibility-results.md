# Compatibility results (Phase 3D)

## Summary

Both isolated Windows environments **failed** initial Qwen3-8B 4-bit load with `0xC0000005` in `torch_cpu.dll` during `from_pretrained`, after tokenizer load succeeded.

| Env | Native CUDA / Linear4bit | Tokenizer | Model load | Generation | 3/3 qual |
| --- | --- | --- | --- | --- | --- |
| Primary 3.13 | pass (Phase 3C) | pass | intermittent / AV | 0 | failed |
| Isolated 3.12 | pass | pass | **AV** | not run | not run |
| Isolated 3.11 | pass | pass | **AV** | not run | not run |

## Implication

Changing Python from 3.13 → 3.12 → 3.11 **did not** clear the access violation when using the same torch 2.6.0+cu124 + transformers 5.14.1 + bitsandbytes 0.49.2 stack on this Windows host. The repeated WER fault offset `0x0000000006046edb` in `torch_cpu.dll` supports a **native PyTorch/Windows load-path** problem more than a Python-3.13-only interpreter bug.

This is **correlation / supported inference**, not a fully proven exclusive root cause.
