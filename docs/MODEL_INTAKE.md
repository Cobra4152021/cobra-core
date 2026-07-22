# Model Intake

## Goal

Record exact identity and integrity metadata for any candidate model **before** baseline evaluation.

## ModelManifest fields

| Field | Purpose |
| --- | --- |
| provider | Family id (`qwen`, `mistral`, `gemma`, …) |
| model_name | Upstream model name |
| model_revision | Exact tag / revision evaluated |
| source_repository | Upstream repository URL/id |
| source_commit | Pinned commit or equivalent |
| license_name / license_url | License clarity |
| artifact_files | Paths + SHA256 hashes |
| parameter_count | Optional size signal |
| architecture | Architecture family string |
| quantization | Method / bits if applicable |
| context_window | Max context tokens |
| acquisition_date | When artifacts were acquired |
| notes | Free-form lab notes |

## Rules

1. Do not download weights in Phase 1 scaffold work.
2. Never commit weights, shards, or GGUF/safetensors blobs to git.
3. Manifests describe artifacts; they are not substitutes for license review.
4. Qwen is first evaluation target, but intake is provider-neutral.
5. Validate manifests with `cobra-validate-manifests` or `python scripts/validate_manifests.py`.

## Example

See `model-cards/EXAMPLE_qwen_manifest.json` — structural example only (`not-acquired`).
