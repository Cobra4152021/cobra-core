# ADR-0013 — WSL2 Linux runtime qualification (Phase 3E)

## Status

Accepted — **Outcome E**.

## Context

Windows PyTorch load of Qwen3-8B (4-bit) repeatedly access-violates. Phase 3D Outcome D directed Linux/WSL2 or cloud migration. Official CobraBench v0.1 score **0.840** remains authoritative for v0.1 only.

## Windows access-violation history

Python 3.11/3.12/3.13 with torch 2.6.0+cu124 crashed in `torch_cpu.dll` during full model load after CUDA/bnb micro-ops passed.

## Why additional Windows retries stopped

Phase 3D exhausted isolated CPython versions without changing the fault signature. Further identical Windows retries were not authorized.

## Why WSL2 was selected before cloud GPU

Reuse the local RTX 4070, avoid cloud charges, and obtain a Linux native library stack for comparison.

## WSL2 environment

* WSL 2.4.13.0 / kernel string 5.15.167.4-1 reported by `wsl --version`.
* `WSLService` Stopped + Disabled.
* Enablement denied without elevation.
* No distribution running; preferred Ubuntu 24.04 not reachable.
* No `.wslconfig` changes.

## Repository-transfer method

Not executed (blocked before Gate 3).

## Model-artifact method

Not executed. Existing local artifacts remain the only authorized source for a future phase.

## Dependency selection

Not installed (no Linux environment).

## Native-backend / load / generation / qualification

Not run. Full-load count: 0.

## Resource findings

Host has ~32 GB RAM and RTX 4070 12 GB; capacity would likely support a future WSL2 attempt if the service can be enabled with elevation. This phase did not modify page files or BIOS.

## Outcome

**E — WSL2 GPU passthrough or installation is unavailable.**

Cloud fallback specification recorded at `evaluations/environments/cloud-gpu-fallback-spec.md`. No runtime candidate created.

## Remaining uncertainty

* Whether elevated enablement of `WSLService` would succeed on this host
* Whether Linux on the same GPU avoids the Windows AV

## Next authorized phase

Cloud GPU qualification (or an elevated WSL2 remediation outside this phase’s non-elevated authorization).

## Required statement

> Phase 3E performs WSL2 runtime qualification only. It does not execute CobraBench, alter the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy a model, or designate Qwen3-8B as Cobra Core.
