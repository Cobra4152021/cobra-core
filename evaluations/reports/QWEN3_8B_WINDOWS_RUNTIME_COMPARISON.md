# Qwen3-8B Windows Runtime Comparison (Phase 3D)

| Field | Primary 3.13 | Isolated 3.12 | Isolated 3.11 |
| --- | --- | --- | --- |
| Interpreter | 3.13.5 | 3.12.10 | 3.11.9 |
| Venv | `.venv` (unchanged) | `.venv-qwen312` | `.venv-qwen311` |
| torch | 2.6.0+cu124 | 2.6.0+cu124 | 2.6.0+cu124 |
| transformers | 5.14.1 | 5.14.1 | 5.14.1 |
| accelerate | 1.14.0 | 1.14.0 | 1.14.0 |
| bitsandbytes | 0.49.2 | 0.49.2 | 0.49.2 |
| CUDA visible / RTX 4070 | yes | yes | yes |
| Linear4bit micro-op | pass | pass | pass |
| Explicit-GPU initial load | intermittent / AV (3C) | **AV** | **AV** |
| Generation | 0 | not run | not run |
| 3/3 qualification | failed | not run | not run |
| WER module | torch_cpu.dll | torch_cpu.dll | torch_cpu.dll |
| Fault offset | `0x…6046edb` | `0x…6046edb` | `0x…6046edb` |

## Interpretation

Do **not** attribute the Phase 3C failure to Python 3.13 alone: comparable stacks on 3.12 and 3.11 also access-violate during model load. Benchmark readiness: **not achieved** on Windows under these configurations.
