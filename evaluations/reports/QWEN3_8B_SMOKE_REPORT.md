# Qwen3-8B Technical Smoke Report (Phase 2B)

**Status:** Technical validation complete for the development baseline.  
**Not CobraBench.** No quality scores are claimed.  
**Not Cobra Core.** This does not designate Qwen3-8B as Cobra Core.

## Acquisition

| Field | Value |
| --- | --- |
| Source | `https://huggingface.co/Qwen/Qwen3-8B` |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| External root | `D:\cobra-models\qwen\qwen3-8b\b968826d9c46dd6066d109eabc6255188de91218\` |
| Total downloaded size | 16,397,462,965 bytes (~15.27 GiB / ~16.40 GB) |
| Artifact count (inventory) | 31 |
| Hash verification | All inventory entries locally SHA256-verified |
| Manifest status | `acquired` (2026-07-22) |
| License preserved | Yes (`LICENSE`, Apache-2.0) |
| Model card preserved | Yes (`README.md`) |

**Note:** Inventory currently includes Hugging Face `.cache/huggingface/download/*.metadata` sidecar files created by the downloader. Weight/config/tokenizer/license files are present and hashed. Future acquisitions should exclude `.cache/**`.

## Hardware / runtime

| Field | Value |
| --- | --- |
| OS | Windows 11 |
| GPU | NVIDIA GeForce RTX 4070 (12282 MiB) |
| Driver | 610.74 |
| Python (smoke venv) | 3.13 + torch `2.6.0+cu124` |
| Selected runtime | Transformers |
| Selected precision | bitsandbytes 4-bit load of official BF16 artifacts |
| Why not native BF16 | Official short-context BF16 footprint ~16GB exceeds 12GB VRAM |

## Smoke results

| Test | Result | Notes |
| --- | --- | --- |
| A Basic response | **PASS** | Exact `COBRA_MODEL_OK` |
| B Structured JSON | **PASS** | Parsed `{"status":"ok","code":1}` (single-sample only) |
| C Context grounding | **PASS** | Answered `SK-42` from synthetic passage |
| D Unsupported claim | **PASS** | Returned `INSUFFICIENT_INFORMATION` |
| E Determinism | **PASS** | Identical outputs under seed=123 / temp=0 (best-effort) |
| F Thinking mode | **PASS** | `enable_thinking` flags recorded; reasoning content present when enabled |

## Performance (indicative)

- Cold load was slow (~5 minutes weight load in this run).
- Short generations after load: roughly **0.8–7 tok/s** depending on prompt (4-bit / first-token effects).
- TTFT not separately instrumented in this adapter version (`null`).

## Limitations / unknowns

- C: system disk was nearly full; CUDA torch required a venv on D:.
- Structured-output reliability is **not** proven beyond one smoke case.
- Determinism under GPU kernels is not a guarantee for all settings.
- No CobraBench categories were scored.
- Qwen3-32B and Thinking-2507 were **not** downloaded.
- No training / LoRA occurred.

## Artifacts

Smoke runs are under gitignored:

`evaluations/results/smoke/<run-id>/`
