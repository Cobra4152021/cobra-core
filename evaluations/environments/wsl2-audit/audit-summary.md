# WSL2 Audit Summary (Phase 3E)

## Result

**WSL2 runtime unavailable for qualification.**

## Evidence

* WSL package reports version **2.4.13.0** / kernel **5.15.167.4-1**.
* `WSLService` is **Stopped** and **Disabled**.
* Non-elevated attempt to set StartType to Manual failed with **Access is denied**.
* `wsl --status`, `wsl -l -v`, and related commands fail with `Wsl/0x80070422`.
* No distributions can be enumerated or selected.
* No `.wslconfig` existed; none was created or modified.
* Host GPU (RTX 4070, driver 610.74) is visible to **Windows** `nvidia-smi`; WSL GPU passthrough could not be tested.

## Preferred distribution (not installed)

Ubuntu 24.04 LTS (fallback Ubuntu 22.04 LTS) — not reachable while the service is disabled.

## Outcome implication

Phase 3E Outcome **E** — WSL2 GPU passthrough or installation is unavailable.
Next authorized phase: cloud GPU qualification (no cloud instance created in this phase).
