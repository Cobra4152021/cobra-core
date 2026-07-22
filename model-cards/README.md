# Model Cards / Manifests

Store `ModelManifest` JSON records for evaluation targets.

## Layout

```text
model-cards/
  qwen/                 # Qwen intake manifests (Phase 2A)
  README.md
```

## Rules

- Do **not** commit model weights.
- Do **not** commit API keys or private tokens.
- Pre-acquisition manifests must use `acquisition_status: not_acquired` and `verification_state: pending` with `sha256: null`.
- Never fabricate SHA256 digests.
- Qwen is the first evaluation family; Mistral/Gemma must use the same schema later.

## Validate

```bash
python scripts/validate_manifests.py
# or
cobra-validate-manifests
```
