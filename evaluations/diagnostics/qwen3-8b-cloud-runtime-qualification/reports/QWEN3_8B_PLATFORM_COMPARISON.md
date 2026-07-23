# Qwen3-8B Platform Comparison (Phase 3F)

| Field | Win 3.13 | Win 3.12 | Win 3.11 | WSL2 | Cloud Linux |
| --- | --- | --- | --- | --- | --- |
| OS | Windows 11 | Windows 11 | Windows 11 | unavailable | not provisioned |
| Python | 3.13.5 | 3.12.10 | 3.11.9 | n/a | planned 3.11/3.12 |
| PyTorch | 2.6.0+cu124 | 2.6.0+cu124 | 2.6.0+cu124 | n/a | proposed 2.6.0+cu124 |
| Native libs | `torch_cpu.dll` | same | same | n/a | `.so` (pending) |
| GPU | RTX 4070 12 GB | same | same | not tested | L4/A5000 authorized (not launched) |
| Model load | AV `0xC0000005` | AV | AV | not attempted | not attempted |
| Generation | 0 | 0 | 0 | n/a | n/a |
| Native crash | yes (`torch_cpu.dll`) | yes | yes | n/a | n/a |
| CUDA errors (caught) | 0 | 0 | 0 | n/a | n/a |
| OOM | 0 | 0 | 0 | n/a | n/a |
| Qualification | failed | failed | failed | blocked | **Outcome F** (auth OK, no API key) |

## Direct observation

* Windows full loads crash in native PyTorch DLL across three CPython versions.
* WSL service cannot start without elevation.
* RunPod spend authorized (L4 ≤ $0.50/hr, $10 ceiling); pod not launched — API key absent.

## Inference

A clean Linux CUDA host is the next viable path to isolate whether the crash is Windows-specific.

## Unresolved cause

Exclusive root cause of the Windows AV remains unproven until a Linux load succeeds or fails under a comparable stack.
