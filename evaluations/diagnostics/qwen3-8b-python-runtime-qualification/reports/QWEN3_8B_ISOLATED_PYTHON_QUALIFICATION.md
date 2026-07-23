# Qwen3-8B Isolated Python Qualification (Phase 3D)

## Phase 3C evidence

Windows `0xC0000005` during Qwen3-8B 4-bit load; WER faulting module `torch_cpu.dll`; Outcome C (narrowed, no stable load). Official v0.1 score **0.840** unchanged.

## Reason for isolation

Python 3.13 was a material compatibility variable. Phase 3D tested side-by-side Python **3.12** and conditional **3.11** without modifying primary `.venv`.

## Environment creation

* Installed Python 3.12.10 and 3.11.9 via winget (user scope); did **not** replace `C:\Python313`.
* Created `.venv-qwen312/` and `.venv-qwen311/` (gitignored).
* Pinned inference stack to match primary where wheels allow (`torch==2.6.0+cu124`, `transformers==5.14.1`, `accelerate==1.14.0`, `bitsandbytes==0.49.2`).
* numpy on 3.11 pinned to `2.2.6` (no 2.5.1 wheel).

## Package / native validation

Both isolated envs: `pip check` clean; CUDA tensor ops OK; bitsandbytes `Linear4bit` micro-op OK; model inventory hash unchanged.

## Attempt table

| Attempt | Env | Mode | Result | Status | Stage |
| --- | --- | --- | --- | --- | --- |
| py312-01-load | 3.12 | load | fail | `0xC0000005` | after tokenizer / `model_load_begin` |
| py311-01-load | 3.11 | load | fail | `0xC0000005` | after tokenizer / `model_load_begin` |

No qualification or extended sessions (initial load gate failed).

## Crash table

| Env | Faulting app | Faulting module | Exception | Offset |
| --- | --- | --- | --- | --- |
| 3.11 | python.exe 3.11.9 | `...\torch\lib\torch_cpu.dll` | `0xc0000005` | `0x0000000006046edb` |
| 3.12 | python.exe 3.12.10 | `...\torch\lib\torch_cpu.dll` | `0xc0000005` | `0x0000000006046edb` |
| 3.13 (historical) | python.exe 3.13.5 | `...\torch\lib\torch_cpu.dll` | `0xc0000005` | `0x0000000006046edb` |

## Totals

* Full-load attempts: **2**
* Access violations: **2**
* Caught CUDA errors: **0**
* Successful loads / generations: **0**

## Root-cause implications

* Python isolation alone is **insufficient** on this host with torch 2.6.0+cu124.
* Identical fault offset across 3.12 and 3.13 increases confidence that the crash is in the **PyTorch native load path on Windows**, not unique to CPython 3.13.
* bitsandbytes remains not proven as sole cause (tiny Linear4bit succeeds).

**Confidence:** medium-high that Windows+torch load path is the blocker; still not exclusive proof of a single upstream bug.

## Qualification outcome

**Outcome D** — both isolated environments fail with native access violations.

## Next authorized phase

Linux, WSL2, or cloud-GPU runtime migration (no CobraBench until a host qualifies).
