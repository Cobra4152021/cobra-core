# Qwen3-8B Windows vs WSL2 Comparison (Phase 3E)

| Field | Windows (3B–3D) | WSL2 (3E) |
| --- | --- | --- |
| Native library platform | Windows DLLs (`torch_cpu.dll`) | Not started |
| Python | 3.13 / 3.12 / 3.11 | n/a |
| PyTorch | 2.6.0+cu124 | n/a |
| bitsandbytes | 0.49.2 | n/a |
| Model load | Access violation `0xC0000005` | Not attempted |
| Generation | 0 successes | Not attempted |
| Fault type | AV in `torch_cpu.dll` @ `0x…6046edb` | Service disabled |
| CUDA errors (caught) | 0 | n/a |
| OOM kills | 0 observed | n/a |
| Load time / VRAM / RAM | Crash before completion | n/a |
| Stability status | Failed | Unavailable |

## Observed evidence

* WSL package bits installed (2.4.13.0) but `WSLService` StartType=Disabled.
* Non-elevated enable attempt: Access denied.
* `wsl` CLI returns `Wsl/0x80070422`.

## Inference

Inability to enter Linux means Phase 3E cannot confirm whether the Windows-specific native crash would disappear under Linux on the same GPU.

## Unresolved cause

Whether the `torch_cpu.dll` fault is Windows-only remains unproven until a Linux (WSL2 with elevation, or cloud GPU) host runs the same load configuration.
