# Qwen3-8B Cloud Linux Runtime Qualification (Phase 3F)

## Windows failure history

Phases 3B–3D: full 4-bit Qwen3-8B load failed on Windows Python 3.11/3.12/3.13 with `0xC0000005` in `torch_cpu.dll` (identical offset). Micro-ops passed; no qualified generation.

## WSL2 service blocker

Phase 3E: WSL 2.4.13.0 present but `WSLService` Disabled; `Wsl/0x80070422`; non-elevated enable denied. Outcome E.

## Cloud authorization

**Not granted.** Status: `ready-for-cloud-authorization` (Outcome **H**).

No provider, GPU SKU, spending ceiling, runtime ceiling, disk size, or region was supplied. **No instance created. Cost: $0.**

## Provider / host / security / transfer

| Item | Status |
| --- | --- |
| Provider | pending authorization |
| Host | not provisioned |
| Security manifest | planned (`evaluations/cloud/security-manifest.json`) |
| Git bundle | `artifacts/cloud-qwen3-runtime-qualification/cobra-core-phase3e.bundle` @ `695ea88…` |
| Model weights in bundle | **no** (checksums only) |
| Model transfer | deferred (encrypted private copy after auth) |

## Linux environment / dependencies / native backend / loads

Not created. Full-load attempts: **0**.

## Qualification / extended session / runtime candidate

Not run. No candidate created.

## Cost / export / cleanup

* Cost record: `no_spend`, total estimated `$0`, ceiling respected.
* Export: local preparation complete; cloud export N/A.
* Cleanup: not applicable (no instance).

## Outcome

**H — Qualification prepared but no cloud spending authorized.**

## Next authorized phase

Provide explicit authorization (provider, GPU, hourly rate, spending ceiling, runtime ceiling, disk, region). Then provision **one** approved host and continue Gates 4–16. Do **not** run CobraBench until a later authorized phase after qualification.

Official v0.1 score **0.840** unchanged. Protocol remains `prepared-not-run`.
