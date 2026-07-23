# ADR-0014 — Cloud Linux runtime qualification (Phase 3F)

## Status

Accepted — **Outcome H** (`ready-for-cloud-authorization`).

## Context

Windows Qwen3-8B 4-bit loads access-violate; WSL2 cannot start in-session. Cloud Linux is the next authorized path. Official CobraBench v0.1 score **0.840** remains authoritative for v0.1 only.

## Windows access-violation history

Identical `torch_cpu.dll` fault offset on Python 3.11/3.12/3.13 with torch 2.6.0+cu124.

## WSL2 service blocker

`WSLService` Disabled; `Wsl/0x80070422`; enable Access denied without elevation (Phase 3E Outcome E).

## Why cloud Linux was selected

Reuse a clean Linux CUDA stack without depending on local WSL service enablement; avoid further Windows retries.

## Authorization boundary

No provider/GPU/spend/runtime/disk/region authorization was provided. Phase 3F **must not** incur charges. Preparation stopped at Gate 2.

## Host selection / security / transfers / dependencies / findings

Deferred until authorization. Transfer package and proposed pin lock prepared locally. No model load, generation, qualification, cost, or cleanup of live resources.

## Outcome

**H — Qualification prepared but no cloud spending authorized.**

## Remaining uncertainty

Whether Linux avoids the Windows native crash; which provider/SKU will be authorized.

## Next authorized phase

Explicit cloud authorization → single-instance provision → Gates 4–16. CobraBench remains unauthorized until a later phase after qualification.

## Required statement

> Phase 3F performs cloud Linux runtime qualification only. It does not execute CobraBench, change the official CobraBench v0.1 score of 0.840, finalize CobraBench v0.2, authorize training, deploy an inference service, or designate Qwen3-8B as Cobra Core.
