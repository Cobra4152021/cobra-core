# ADR-0011 — Qwen3-8B Windows load remediation (Phase 3C)

## Status

Accepted — Outcome **C** (root cause narrowed; no smoke-qualified stable runtime).

## Context

Phase 3B blocked the experimental CobraBench v0.2-rc2 evaluation because Qwen3-8B 4-bit load crashed twice with Windows `0xC0000005` during weight loading. Official CobraBench v0.1 score **0.840** remains authoritative for v0.1 only.

## Phase 3B failure

* Model revision `b968826d9c46dd6066d109eabc6255188de91218`
* 4-bit NF4 / double quant / float16 compute / `device_map=auto`
* Crash ~75% through 399 modules; no generation; no benchmark cases

## Diagnostic scope

Phase 3C performed subprocess-isolated load diagnostics only:

* evidence preservation,
* file integrity,
* bitsandbytes micro-diagnostics,
* host readiness,
* ≤6 live load attempts,
* smoke qualification attempts,
* **no** CobraBench execution.

## Model integrity

Local artifacts passed integrity checks (sizes vs Phase 3B inventory; safetensors headers open). **Outcome E not selected.**

## Host environment

* Windows 11, RTX 4070 12 GB, driver 610.74, CUDA 12.4 (torch build)
* Desktop GPU use ~2.2 GiB throughout
* System RAM ~34 GB; available often 12–15+ GB during attempts
* Page-file headroom appeared adequate; not modified

## Package compatibility

Primary `.venv` retained: Python 3.13.5, torch 2.6.0+cu124, transformers 5.14.1, accelerate 1.14.0, bitsandbytes 0.49.2. No in-place downgrade. No `.venv-load-diagnostic/` created in this phase.

## Quantization findings

bitsandbytes imports and a tiny CUDA `Linear4bit` operation succeed. Full Qwen3-8B 4-bit load still crashes frequently. Quantization alone is not a proven exclusive root cause.

## Device-map findings

* `device_map=auto` with CPU offload (**A**): access violation (reproduces Phase 3B).
* Explicit `{"": 0}` (**B**): one successful load; subsequent QUAL loads with the same mapping crashed.

## Memory findings

Failures occurred even when free VRAM ~9.7 GiB and available RAM ≥14 GiB at process start. Memory pressure remains a possible contributor during materialization but is not a complete explanation.

## Smoke qualification

**Failed.** 0 successful QUAL load+generation cycles. See `evaluations/reports/QWEN3_8B_SMOKE_QUALIFICATION.md`.

## Outcome

**C — Root cause narrowed but no stable load.**

Windows Error Reporting repeatedly cites faulting module **`torch_cpu.dll`** (also `c10.dll`) with exception `0xc0000005` in `python.exe` 3.13.x.

## Remaining uncertainty

* Whether Python 3.12/3.11 isolation would stabilize loads
* Whether a Linux/WSL2 host would avoid the fault
* Whether a specific Transformers/Accelerate offload interaction is necessary and sufficient
* Whether endpoint security scanning contributes (not tested; AV not disabled)

## Next authorized options

1. Isolated Python 3.11/3.12 compatibility environment + re-qualification (Outcome B path)
2. Alternate host (Linux/WSL2/cloud GPU)
3. Deeper native crash analysis with separately authorized tooling
4. Only after `smoke-qualified`: authorize Phase 3D rc2 evaluation

## Decision statement

> Phase 3C does not execute CobraBench, modify the official 0.840 score, finalize CobraBench v0.2, authorize training, or designate Qwen3-8B as Cobra Core.
