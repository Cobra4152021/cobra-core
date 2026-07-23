# Phase 3C — Source Evidence Index

**Directory:** `evaluations/diagnostics/qwen3-8b-windows-load-isolation/`  
**Phase 3B commit:** `923c006785bfee72ff85d1f8029f40cd3791b4dd`  
**Official CobraBench v0.1 score (unchanged):** `0.840`

## Preserved Phase 3B artifacts

| Artifact | Path under `phase3b-evidence/` |
| --- | --- |
| Preflight | `qwen3-8b-v0.2-rc2-preflight.json` |
| Model inventory | `qwen3-8b-local-inventory.json` |
| Smoke attempt 1 crash | `smoke_attempt1_crash.json` |
| Smoke attempt 2 log | `smoke_attempt2.log` |
| Smoke result | `smoke_result.json` |
| Smoke summary | `SMOKE.md` |
| ADR-0010 | `ADR-0010-qwen3-8b-rc2-experimental-evaluation.md` |
| Phase 3B summary | `QWEN3_8B_COBRABENCH_V0_2_RC2_SUMMARY.md` |

Phase 3B originals under `evaluations/` were **not overwritten**.

## Known (evidence-backed)

* Model loading reached approximately **75%** of 399 modules (progress bars in attempt-2 log).
* Process terminated with Windows status **`0xC0000005`** (ACCESS_VIOLATION).
* No Python exception was captured by the parent script.
* No benchmark generation occurred; no rc2 cases started.
* Desktop GPU use was approximately **2.3 GiB** before the Phase 3B retry (`nvidia-smi`).
* One environmental retry with tighter `max_memory` failed similarly.
* Same host previously saw `0xC0000005` during Phase 2E diagnostics and Qwen3-32B feasibility.

## Unknown (not labeled as root cause)

* Whether failure originates in bitsandbytes native code
* Whether failure originates in Python 3.13 compatibility
* Whether failure originates in Transformers 5.x
* Whether failure originates in host RAM pressure
* Whether failure originates in Windows page-file pressure
* Whether `device_map=auto` causes unstable offloading
* Whether a specific model shard or layer triggers the crash
* Whether antivirus or endpoint scanning contributes
* Whether GPU driver instability contributes

## Frozen artifacts (must remain unchanged)

* Official score `0.840` / baseline inventory `84b0972f…1de6`
* rc1 / rc2 inventory and tree hashes
* Prepared protocol status `prepared-not-run`
