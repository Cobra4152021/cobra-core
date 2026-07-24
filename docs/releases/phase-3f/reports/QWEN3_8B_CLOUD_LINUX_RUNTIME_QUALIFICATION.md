# Qwen3-8B Cloud Linux Runtime Qualification (Phase 3F)

## Windows failure history

Phases 3B–3D: full 4-bit Qwen3-8B load failed on Windows Python 3.11/3.12/3.13 with `0xC0000005` in `torch_cpu.dll`.

## WSL2 service blocker

Phase 3E Outcome E: `WSLService` Disabled (`Wsl/0x80070422`).

## Cloud authorization

Authorized RunPod Community Cloud with $10 / 8h ceilings. Existing pod adopted (no new launch).

| Field | Value |
| --- | --- |
| Provider | RunPod Community Cloud GPU Pod |
| Pod ID | `txw75nv9hn96hu` |
| GPU | NVIDIA A40 48 GB |
| Displayed rate | **$0.44/hr** |
| System RAM | 50 GB |
| Python | 3.12.3 |
| PyTorch | 2.6.0+cu124 |
| Transformers | 5.14.1 |
| CUDA available | True |

## Qualification results

| Gate | Result |
| --- | --- |
| Native backend | pass |
| Initial load | pass (74.777s) |
| Initial generation | pass |
| 3/3 fresh-process qualification | pass |
| Extended session (5 prompts) | pass |
| Full loads used | 6 / 6 |
| Peak VRAM | 6318342144 bytes (~5.88 GiB) |
| CobraBench | **not executed** (`prepared-not-run`) |
| Official v0.1 score | **0.840** unchanged |

## Dependency lock correction

Draft lock pinned `huggingface-hub==0.34.4`, which conflicts with `transformers==5.14.1` (`huggingface-hub>=1.5.0`). Lock corrected to `huggingface-hub==1.24.0` to match the validated Python 3.12 freeze before install.

## Cost / cleanup

* Estimated runtime: **3.14 h**
* Estimated compute cost: **$1.38** (ceiling $10.00 respected)
* Pod terminated: **True**
* Remaining billable resources: `[]`

## Outcome

**A — Cloud Linux runtime fully qualified**

Runtime candidate: `evaluations/runtime-candidates/qwen3-8b-cloud-linux-qualified.json`

Next authorized phase: Phase 3G controlled CobraBench v0.2-rc2 on the locked cloud runtime (not executed here).

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
