# Security

## Non-negotiables

- No API keys, tokens, or credentials in git.
- No model weights in git.
- No private evidence, proprietary datasets, or active-case material in git.
- No production chat endpoints in this repository.
- Training remains disabled until Phase 5 approval after baseline evaluation.

## Secrets

- Use `.env` locally (gitignored).
- Start from `.env.example` (placeholders only).

## Evaluation outputs

`evaluations/results/` and most of `evaluations/reports/` are gitignored so raw model outputs that might later include sensitive material are not committed by accident. Commit only templates and public documentation.

## Datasets

`datasets/raw/` and `datasets/curated/` ignore contents by default. Only synthetic/public-safe materials should ever be force-added, and only after review.

## LLM-as-judge caution

LLM-as-judge outputs may contain regurgitated prompt content. Treat them as advisory artifacts, redacted when needed, and never as sole ground truth.

## Model weights and prompts

- Weights live only under `COBRA_MODEL_HOME` (default `D:\cobra-models`), never in git.
- Acquisition logs must not print tokens or Authorization headers.
- Smoke-run prompts are synthetic and gitignored under `evaluations/results/`.
- Do not commit private investigation prompts or evidence.

## Scope boundary

This lab must not grow into a shadow Investigator app. Auth, billing, Evidence Vault, and case management belong in `cobra-investigator`, not here.
