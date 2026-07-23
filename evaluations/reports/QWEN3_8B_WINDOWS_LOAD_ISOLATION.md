# Qwen3-8B Windows Load Isolation (Phase 3C)

## Initial failure (Phase 3B)

Hard Windows process crash `0xC0000005` during 4-bit Qwen3-8B load (~75% of 399 modules), twice. No Python exception. No generation. No benchmark.

## Known evidence

* Crash reproduced under subprocess capture (configuration `A`).
* Safetensors / tokenizer / config integrity: **pass** (no corruption).
* bitsandbytes import + tiny `Linear4bit` CUDA op: **pass**.
* Metadata/safetensors scan (configuration `E`): **pass**.
* Windows Application Error events name faulting modules **`torch_cpu.dll`** (and historically `c10.dll`), exception `0xc0000005`, faulting application `python.exe` 3.13.x.
* One load-only success with explicit GPU `device_map={"": 0}` (configuration `B`).
* Four subsequent QUAL loads with the same GPU mapping crashed with `0xC0000005`.

## Diagnostic method

* Parent orchestrator: `scripts/diagnose_qwen3_8b_load.py`
* Child worker: `scripts/_qwen3_8b_load_worker.py`
* Each attempt in an isolated subprocess; parent survives child AV
* Progress JSONL + host snapshots flushed per attempt
* Live model loads capped at **6**

## Configuration matrix

| ID | Intent | Result |
| --- | --- | --- |
| E | Metadata / safetensors open (not a live weight load) | **success** |
| A | Reproduce known failure (`device_map=auto` + CPU offload) | **AV `0xC0000005`** |
| B | Explicit GPU, no offload | **load success** (no generation) |
| C | Reduced auto-offload pressure | not run (B succeeded; budget reserved for QUAL) |
| D | 8-bit diagnostic | not run (budget reserved for QUAL) |
| F | Isolated compat venv | not created (no stable primary path; no alternate Python provisioned in-phase) |

## Attempts (live loads)

| Attempt | Config | Success | Status | Starting VRAM free (MiB) | Starting RAM avail (bytes) |
| --- | --- | --- | --- | ---: | ---: |
| 02 | A | no | `0xC0000005` | 9772 | 12424204288 |
| 03 | B | yes (load) | `0x00000000` | 9802 | 14828158976 |
| 04 | QUAL | no | `0xC0000005` | 9801 | 15314505728 |
| 05 | QUAL | no | `0xC0000005` | 9741 | 15498604544 |
| 06 | QUAL | no | `0xC0000005` | 9770 | 15639851008 |
| 07 | QUAL | no | `0xC0000005` | 9758 | 15863894016 |

Access-violation count (live): **5** (A + 4×QUAL)  
Successful loads: **1** (B only)  
Successful generations: **0**  
CUDA errors caught: **0**

## File-integrity findings

`evaluations/model-inventory/qwen3-8b-file-integrity.json` → **pass**. No Outcome E.

## bitsandbytes findings

Import OK; Linear4bit micro-op OK. **Not sufficient** to blame bitsandbytes alone. See `BITSANDBYTES_WINDOWS_DIAGNOSTIC.md`.

## Python compatibility findings

Python **3.13.5** remains a material risk. Crashes fault inside **PyTorch** native libs (`torch_cpu.dll`). Isolated 3.11/3.12 environment was **not** created in Phase 3C because:

* primary `.venv` must remain immutable,
* no alternate interpreter was provisioned/authorized mid-phase,
* attempt budget was consumed measuring intermittency of configuration B/QUAL.

## Device-map / memory findings

* `device_map=auto` + CPU offload path (**A**) consistently crashed (matches Phase 3B).
* Explicit GPU mapping (**B**) can complete a load, but is **not stable** across repeated subprocesses.
* Desktop GPU occupancy remained ~2.2 GiB; available system RAM during QUAL was often ≥14 GiB — failures still occurred, so simple “low free RAM at start” is **not** a complete explanation.
* Page file headroom appeared adequate (~16–17 GiB available); no silent page-file change was made.

## Successful configurations

* **E** (metadata) — always OK
* **B** — one-time load success only

## Failed configurations

* **A**, **QUAL** (×4)

## Repeated smoke results

See `QWEN3_8B_SMOKE_QUALIFICATION.md` — **failed** (0/3+).

## Root-cause assessment

**Narrowed, not proven.**

Most supported statements:

1. Crash is a hard native access violation in the Python/PyTorch stack (`torch_cpu.dll` / `c10.dll`), not a catchable CUDA Python exception.
2. The Phase 3B-style `device_map=auto` + offload configuration remains a reliable reproducer.
3. Explicit single-GPU placement removes the auto-offload factor but does **not** yield a smoke-qualified stable runtime on this host/environment.
4. Model files are not corrupt; tiny bitsandbytes ops can succeed.

Residual hypotheses (still open): Python 3.13 + torch/bnb Windows interaction; Transformers 5.x load path; driver/WDDM interaction; intermittent allocator / commit-charge stress during large 4-bit materialization.

**Root-cause confidence:** **medium** for “PyTorch native path during large model load on this Windows+Py3.13 stack”; **low** for any single library as exclusive root cause.

## Outcome

**Outcome C — Root cause narrowed but no stable load.**

## Next authorized step

Targeted remediation phase options (require separate authorization):

* Provision isolated Python 3.11/3.12 venv with locked torch/transformers/bnb versions and re-run smoke qualification only
* Evaluate on WSL2/Linux or another GPU host
* Further torch/CPU-offload isolation with debugger-grade tooling (not installed in 3C)

**Do not** execute CobraBench rc2 until a configuration is `smoke-qualified`.
