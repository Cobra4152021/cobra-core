# Qwen3-8B Smoke Qualification (Phase 3C)

**Decision:** **not qualified** (`failed`)  
**Benchmark execution:** not authorized / not performed  
**Prepared rc2 protocol:** remains `prepared-not-run`

## Candidate configuration under test

| Field | Value |
| --- | --- |
| Configuration ID | `QUAL` (same load path as successful matrix `B`) |
| Quantization | bitsandbytes 4-bit NF4, double quant, float16 compute |
| device_map | `{"": 0}` (explicit single-GPU, no CPU offload) |
| max_memory | none |
| low_cpu_mem_usage | true |
| offload_state_dict | false |
| trust_remote_code | false |
| Generation | synthetic non-benchmark prompt (`SMOKE_PROMPT`) |
| Environment | primary `.venv` / Python 3.13.5 |

## Prior load-only success (not a smoke qualification)

| Attempt | Result | Notes |
| --- | --- | --- |
| `attempt-03-B` | **load success** | Tokenizer + model load completed (~239 s). No generation. |

## Three-run smoke table (QUAL)

| Run | Attempt ID | Load | Generation | Exit | Windows status | Peak VRAM |
| ---: | --- | --- | --- | ---: | --- | --- |
| 1 | `attempt-04-QUAL` | fail | n/a | 3221225477 | `0xC0000005` | n/a |
| 2 | `attempt-05-QUAL` | fail | n/a | 3221225477 | `0xC0000005` | n/a |
| 3 | `attempt-06-QUAL` | fail | n/a | 3221225477 | `0xC0000005` | n/a |

Additional intermittency sample within the live-load ceiling:

| Run | Attempt ID | Load | Generation | Exit | Windows status |
| ---: | --- | --- | --- | ---: | --- |
| 4 | `attempt-07-QUAL` | fail | n/a | 3221225477 | `0xC0000005` |

## Totals

| Metric | Value |
| --- | --- |
| QUAL successes | **0** |
| QUAL access violations | **4** |
| CUDA errors caught in Python | **0** |
| Corrupted outputs | **0** (no generation completed) |
| Qualification status | `failed` (not `smoke-qualified`, not merely `unstable`) |

## Qualification decision

**Fail.** Requirements for `smoke-qualified` (3/3 isolated load+generation successes, 0 access violations) were not met.

A single prior load-only success on configuration `B` is insufficient and was not reproducible under the QUAL subprocess series.
