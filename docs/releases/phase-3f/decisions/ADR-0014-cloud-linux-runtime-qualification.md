# ADR-0014 — Cloud Linux runtime qualification (Phase 3F)

## Status

Accepted — **Outcome A** (cloud Linux runtime fully qualified). Prior states: H → F (credentials/SSH) → A.

## Context

Windows Qwen3-8B loads access-violate; WSL2 unavailable. Cloud Linux on RunPod was authorized for qualification only.

## Windows access-violation history

Identical `torch_cpu.dll` fault across Python 3.11/3.12/3.13.

## WSL2 service blocker

Phase 3E Outcome E.

## Why cloud Linux was selected

Clean Linux CUDA path without local WSL enablement.

## Authorization boundary

User authorized RunPod Community Cloud with $10 / 8h ceilings. Existing manual pod `txw75nv9hn96hu` (A40 @ $0.44/hr) was adopted; no second pod created.

## Host selection

Adopted running A40 pod within spending ceiling after L4 primary was unavailable in the live session.

## Security posture

SSH over exposed TCP with account-registered keys after `PUBLIC_KEY` injection. No public inference endpoint created. No secrets committed.

## Repository / model transfer / dependencies / load / generation / qualification

* Bundle restored at `695ea8833229b183e5792c49e3888ec4dde9e5f2`
* Model inventory `8cf07aa84c9e26c9dd4ce71b21bd498232c8dfa5afe5284d375be0c1e9bb3f4f` verified on-host
* Pinned torch `2.6.0+cu124` + transformers `5.14.1`
* 6/6 full-load subprocesses succeeded (load, generate, 3× qual, extended)

## Cost / cleanup

Estimated ~$1.38 over ~3.14 h. Pod terminated after export. Remaining billable resources: none.

## Outcome

**A — Cloud Linux runtime fully qualified.**

## Remaining uncertainty

CobraBench behavior on this runtime is not yet measured (Phase 3G).

## Next authorized phase

Phase 3G — controlled CobraBench v0.2-rc2 on the locked cloud runtime. CobraBench remains unauthorized until that phase.

## Required statement

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
