# Qwen3-8B WSL2 Runtime Qualification (Phase 3E)

## Windows failure history

Phases 3B–3D: Qwen3-8B 4-bit full load failed on Windows Python 3.13 / 3.12 / 3.11 with `0xC0000005` in `torch_cpu.dll` (identical fault offset). CUDA and bitsandbytes micro-ops passed. Official CobraBench v0.1 score **0.840** unchanged.

## Reason WSL2 was selected

Phase 3D Outcome D authorized Linux/WSL2/cloud migration before further Windows retries. WSL2 was preferred first to reuse the local RTX 4070 without cloud charges.

## WSL version

* WSL package: **2.4.13.0**
* Reported kernel: **5.15.167.4-1**
* WSLg: 1.0.65

## Distribution / kernel (inside Linux)

Not obtained — `WSLService` is **Disabled**; `wsl` fails with `Wsl/0x80070422`. Preferred Ubuntu 24.04 LTS was not installable in this session.

## GPU passthrough

**Unavailable.** Host Windows `nvidia-smi` sees RTX 4070 / driver 610.74. No WSL `nvidia-smi` possible while the service is stopped/disabled.

## Repository transfer / model access

Not performed (blocked at Gate 2). Required Windows commit for any future WSL copy: `9ea6874f3edb71fb2734c427079dd454c5d75b59`. Model revision/inventory remain frozen; no redownload.

## Dependency stack / native backend / loads

Not created. Full-load attempts: **0**.

## Qualification / extended session

Not run.

## Resource / filesystem findings

* Host RAM ~32 GB; free ~12 GB at audit.
* Page files on C: and H: present.
* Disk D: has ample free space for a future Linux copy.
* No `.wslconfig` present; none modified.

## Comparison with Windows

Windows native stack can import torch/CUDA/bnb but crashes on full load. WSL2 Linux stack could not be started for comparison.

## Selected outcome

**Outcome E** — WSL2 GPU passthrough or installation is unavailable.

## Next authorized phase

Cloud GPU qualification (specification only prepared in this phase; no instance created).

## Required confirmation

No CobraBench execution. Prepared rc2 protocol remains `prepared-not-run`. Score **0.840** unchanged.
