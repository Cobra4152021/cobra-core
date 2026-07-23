# Cloud GPU Fallback Specification (Phase 3E)

Prepared because WSL2 runtime qualification could not proceed (Outcome E: WSLService disabled / `Wsl/0x80070422`).

**No cloud instance was created. No charges were incurred.**

## Minimum requested environment

| Requirement | Minimum |
| --- | --- |
| OS | Linux |
| GPU | NVIDIA, CUDA-capable |
| VRAM | ≥ 16 GB |
| System RAM | ≥ 32 GB |
| Disk | ≥ 100 GB |
| Python | 3.11 or 3.12 (not 3.13 for initial matrix) |
| PyTorch | Stable CUDA-compatible wheel (no nightly) |
| Network | Outbound disabled after required setup where practical |
| Storage | Encrypted where available |
| Artifacts | No persistent model/eval leftovers after export |

## Preferred GPU classes (examples)

* NVIDIA L4
* NVIDIA A10
* NVIDIA A4000 / A5000
* NVIDIA RTX 4090
* Equivalent or better

## Model policy

* Reuse validated Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`
* Inventory hash `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f`
* Transfer by controlled copy or signed offline bundle — not an unsupervised Hugging Face redownload
* Do not designate Cobra Core

## Evaluation policy

* Qualify load + synthetic smoke before any CobraBench run
* Official CobraBench v0.1 score `0.840` remains authoritative for v0.1 only
* Prepared rc2 protocol remains `prepared-not-run` until a later authorized phase

## Vendor selection

Deferred. Do not select a vendor or incur charges in Phase 3E.
