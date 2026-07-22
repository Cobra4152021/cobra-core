# Qwen Acquisition Runbook (Phase 2B)

## Scope

Acquire and verify **Qwen3-8B** only:

- Repo: `Qwen/Qwen3-8B`
- Revision: `b968826d9c46dd6066d109eabc6255188de91218`

Do not acquire Qwen3-32B or the reasoning challenger in this phase.

## Commands

```bash
python scripts/preflight_environment.py
python scripts/acquire_model.py --manifest model-cards/qwen/qwen3-8b.manifest.json
python scripts/verify_model.py --manifest model-cards/qwen/qwen3-8b.manifest.json
python scripts/run_smoke_tests.py --manifest model-cards/qwen/qwen3-8b.manifest.json
```

Optional cleanup of quarantined trees:

```bash
python scripts/cleanup_model.py --manifest model-cards/qwen/qwen3-8b.manifest.json --confirm
```

## Storage

Weights land under `%COBRA_MODEL_HOME%` (default `D:\cobra-models`). See `docs/MODEL_STORAGE.md`.

## Failure behavior

Incomplete downloads, missing LICENSE, or hash failures quarantine the acquisition. Quarantined trees cannot be loaded by the inference engine.
