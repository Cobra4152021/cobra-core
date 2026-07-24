# Qwen3-8B Platform Comparison (Phase 3F)

| Platform | Load | Generate | 3/3 qual | Extended | Outcome |
| --- | --- | --- | --- | --- | --- |
| Windows isolated Python 3.11/3.12/3.13 | fail (`torch_cpu.dll` AV) | n/a | n/a | n/a | fail |
| WSL2 | unavailable (`Wsl/0x80070422`) | n/a | n/a | n/a | E |
| Cloud Linux (RunPod A40) | pass | pass | pass | pass | **A** |

Official CobraBench v0.1 score remains **0.840**. Protocol remains `prepared-not-run`.
