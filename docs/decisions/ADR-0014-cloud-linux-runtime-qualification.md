# ADR-0014 — Cloud Linux runtime qualification (Phase 3F)

## Status

Accepted — **Outcome F** after authorization (credentials missing). Prior preparation state was Outcome H.

## Context

Windows Qwen3-8B loads access-violate; WSL2 unavailable. Cloud Linux on RunPod was authorized for qualification only.

## Windows access-violation history

Identical `torch_cpu.dll` fault across Python 3.11/3.12/3.13.

## WSL2 service blocker

Phase 3E Outcome E.

## Why cloud Linux was selected

Clean Linux CUDA path without local WSL enablement.

## Authorization boundary

User authorized RunPod Community Cloud: NVIDIA L4 (≤ $0.50/hr) with RTX A5000 fallback (≤ $0.35/hr), $10 total, 8 hours, ≤ 100 GB, US region preferred, on-demand only, one instance, no spot/public endpoint/Jupyter/autoscaling/multi-GPU/persistent volume beyond session.

Recorded in `evaluations/cloud/authorization-record.json`.

## Host selection

Not completed. Public price precheck: L4 Community **$0.44/hr** within limit. Live displayed price must be re-checked at launch.

## Security posture

No API key committed. No ports opened. No instance created.

## Repository / model transfer / dependencies / load / generation / qualification

Not executed (blocked before provision).

## Cost / cleanup

$0 spend. No billable resources.

## Outcome

**F — Cloud provisioning blocked** due to missing `RUNPOD_API_KEY`.

## Remaining uncertainty

Whether Linux on L4/A5000 avoids the Windows native crash.

## Next authorized phase

Supply RunPod API credentials to the environment and resume single-pod qualification under the recorded ceilings. CobraBench remains unauthorized.

## Required statement

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
