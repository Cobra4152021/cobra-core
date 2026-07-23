# ADR-0012 — Isolated Python runtime qualification (Phase 3D)

## Status

Accepted — **Outcome D**.

## Context

Phases 3B–3C blocked experimental CobraBench v0.2-rc2 evaluation due to hard Windows `0xC0000005` crashes while loading Qwen3-8B (4-bit). Official CobraBench v0.1 score **0.840** remains authoritative for v0.1 only.

## Phase 3B and 3C failures

* Crashes during weight load; WER cites `torch_cpu.dll`.
* Explicit GPU mapping loaded once then failed repeatedly under 3.13.
* Model files intact; tiny bitsandbytes ops succeed.

## Why the primary environment was preserved

Primary `.venv` / Python 3.13 remains the development and quality-suite environment. Phase 3D forbids mutating it; a full snapshot was recorded under `evaluations/environments/primary-python313-snapshot/`.

## Why Python 3.12 was tested first

Newest mainstream scientific-wheel baseline before 3.13; preferred isolation target in the phase plan.

## Why Python 3.11 was conditional

Created only after Python 3.12 **failed** initial load (phase Gate 9).

## Dependency selection

Pinned torch/transformers/accelerate/bitsandbytes to match primary for fair Python comparison. Torch wheels from the official cu124 index. No nightlies; no source builds.

## Native-library findings

Isolated 3.12 inventory recorded (`native_library_inventory_hash` in environment matrix). Crashes still fault inside environment-local `torch_cpu.dll`.

## Model-load findings

| Env | Initial load |
| --- | --- |
| 3.12 | AV during `from_pretrained` after tokenizer |
| 3.11 | AV during `from_pretrained` after tokenizer |

## Generation findings

Not reached (load gate failed).

## Qualification decision

Neither environment is `smoke-qualified`. No runtime candidate created. No extended session.

## Remaining uncertainty

* Whether Linux/WSL2 avoids the fault
* Whether a different torch CUDA build (non-cu124, or older 2.5.x) would change behavior (not authorized to expand matrix beyond attempt budget after dual AV)
* Whether WDDM/desktop GPU contention is necessary

## Selected outcome

**D — Both isolated environments fail with native access violations.**

## Next authorized step

Linux, WSL2, or cloud-GPU runtime migration — then re-qualify before any rc2 evaluation.

## Required statement

> Phase 3D performs runtime qualification only. It does not execute CobraBench, alter the official 0.840 score, finalize CobraBench v0.2, authorize training, or designate Qwen3-8B as Cobra Core.
