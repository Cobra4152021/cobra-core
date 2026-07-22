# Qwen

First evaluation family for CobraBench.

## Phase 2A intake (no weights)

| Role | Model | Manifest |
| --- | --- | --- |
| Primary baseline | Qwen3-32B | `model-cards/qwen/qwen3-32b.manifest.json` |
| Development / CI | Qwen3-8B | `model-cards/qwen/qwen3-8b.manifest.json` |
| Reasoning challenger | Qwen3-30B-A3B-Thinking-2507 | `model-cards/qwen/qwen3-30b-a3b-thinking-2507.manifest.json` |

- Interface: `cobra_core.providers.qwen.QwenProvider` (still unconfigured)
- Status: **intake complete / not acquired**
- Weights: **not downloaded**
- Decision: `docs/decisions/ADR-0001-qwen-baseline-selection.md`
