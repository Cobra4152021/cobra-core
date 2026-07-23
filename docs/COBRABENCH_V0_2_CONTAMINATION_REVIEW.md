# CobraBench v0.2-rc1 Contamination Review

**Reviewer process:** single-reviewer static provenance review  
**Case count:** 46  
**Date:** 2026-07-22

## Aggregate provenance

| Field | Value |
| --- | --- |
| Synthetic authored | 46 |
| Public-domain transform | 0 |
| Permissive transform | 0 |
| Private / confidential | 0 |
| Pretraining exposure risk | low (all synthetic) |
| Answer leakage risk | low (no gold answers in prompts) |

## Checks performed

* Exact duplicate case_id / title detection — pass
* Near-duplicate title detection — pass
* Similarity to CobraBench v0.1 — cases are newly authored with `cb2-` IDs; no copied v0.1 JSON
* Answer-cue inspection (`the correct answer is`, etc.) — pass via validator
* Repeated-template inspection — shared system prompt by design; task prompts unique

## Training-set exclusion

All rc1 cases are labeled:

`exclude_from_future_training_corpora`

Do not publish case contents externally at this stage.

## Per-case metadata

Embedded in each case under `contamination` and summarized in release `human-review-summary.json`.
