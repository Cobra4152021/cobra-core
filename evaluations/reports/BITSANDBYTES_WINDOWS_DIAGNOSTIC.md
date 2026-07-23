# bitsandbytes Windows Diagnostic (Phase 3C)

**Timestamp:** 2026-07-23T05:54:19.046968+00:00

## Summary

| Item | Value |
| --- | --- |
| Import | `pass` |
| bitsandbytes | `0.49.2` |
| torch | `2.6.0+cu124` |
| CUDA available | `True` |
| torch CUDA | `12.4` |
| GPU | `NVIDIA GeForce RTX 4070` |
| Compute capability | `8.9` |
| Linear4bit smoke | `{'ok': True, 'out_shape': [2, 64], 'out_dtype': 'torch.float16'}` |

## Warnings

- none

## Errors

- none

## Interpretation note

Presence of bitsandbytes does **not** prove it caused the Qwen3-8B `0xC0000005` crash.
This report only records whether the backend initializes and whether a tiny Linear4bit op succeeds.
