# Model Intake

## Goal

Record exact identity and integrity metadata for any candidate model **before** baseline evaluation.

## ModelManifest fields

| Field | Purpose |
| --- | --- |
| provider | Family id (`qwen`, `mistral`, `gemma`, …) |
| model_name | Upstream model name |
| model_revision | Exact tag / revision / Hub commit evaluated |
| source_repository | Upstream repository URL/id |
| source_commit | Pinned commit SHA |
| license_name / license_url | License clarity (URL required) |
| artifact_files | Paths + hash verification state (+ SHA256 when known) |
| parameter_count | Optional size signal |
| architecture | `transformer-decoder` or `transformer-decoder-moe` |
| quantization | Method / bits if applicable |
| context_window | Claimed context tokens |
| context_window_provenance | Required citation for the context claim |
| acquisition_status | `not_acquired` / `acquired` / `quarantined` / `failed` |
| intake_date | When the intake record was created |
| acquisition_date | When weights were acquired (null if not acquired) |
| notes | Free-form lab notes |

## Pre-acquisition rules

1. `acquisition_status` must be `not_acquired`.
2. Every artifact `verification_state` must be `pending`.
3. Every artifact `sha256` must be `null`.
4. Placeholder / example digests are rejected.
5. Unpinned revisions (`main`, `latest`, `not-acquired`, …) are rejected.
6. Do not download weights during intake-only milestones.

## Post-acquisition rules

1. Every required artifact must have `verified` or `official` SHA256.
2. `acquisition_date` must be set.
3. Failed integrity checks move the tree to quarantine and set `quarantined` / `failed`.

## Current Qwen intake

See:

- `docs/QWEN_CANDIDATE_ANALYSIS.md`
- `docs/QWEN_ACQUISITION_PLAN.md`
- `docs/decisions/ADR-0001-qwen-baseline-selection.md`
- `model-cards/qwen/*.manifest.json`

## Validate

```bash
python scripts/validate_manifests.py
```
