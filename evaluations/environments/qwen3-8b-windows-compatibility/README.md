# Qwen3-8B Windows compatibility environments (Phase 3D)

Isolated runtimes for diagnosing Windows load crashes without modifying primary `.venv` (Python 3.13).

| Environment | Path | Status |
| --- | --- | --- |
| Primary snapshot | `../primary-python313-snapshot/` | preserved, unmodified |
| Python 3.12 | `.venv-qwen312/` (gitignored) | created; **initial load AV** |
| Python 3.11 | `.venv-qwen311/` (gitignored) | created; **initial load AV** |

See `selection-rationale.md`, `creation-commands.md`, and `compatibility-results.md`.
