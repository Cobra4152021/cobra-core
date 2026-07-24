# Architecture — Cobra Model Lab

## Purpose

Cobra Model Lab is the research, benchmarking, evaluation, and future training foundation for **Cobra Core**, an evidence-first open AI model focused on investigation, research, source analysis, contradiction detection, citation discipline, and hallucination resistance.

This repository is **not** the Cobra Investigator application.

## Separation from Cobra Investigator

| Concern | Cobra Core (this repo) | Cobra Investigator |
| --- | --- | --- |
| Mission | Model research & evaluation | Product application |
| UI / auth / billing | Out of scope | Application concern |
| Case management / Evidence Vault | Out of scope | Application concern |
| Production chat endpoints | Out of scope | Application concern |
| Benchmarks & manifests | In scope | Consumes future models |

## Phase 1 layout

```
benchmarks/     CobraBench cases, rubrics, JSON schemas
datasets/       Raw/curated dataset roots (no proprietary data committed)
evaluations/    Results & reports (gitignored outputs; templates committed)
inference/      Provider-neutral runner stubs
model-cards/    ModelManifest records (no weights)
providers/      Provider notes; code interfaces live in src/cobra_core/providers
training/       Non-operational guards until Phase 5
adapters/       Future LoRA adapter metadata home (empty in Phase 1)
scripts/        Validation and quality-gate helpers
src/cobra_core/ Installable Python package (schemas, CLI, providers)
tests/          Unit tests
docs/           Architecture, CobraBench, intake, security
```

## Core concepts

1. **ModelManifest** — provenance and integrity metadata for a candidate model revision.
2. **BenchmarkCase** — synthetic evaluation scenario with sources, expected/prohibited behaviors, and rubric reference.
3. **EvaluationRun** — preserved record of prompts, revision, inference settings, raw output location, scores, and rationale.

## Provider neutrality

Interfaces do not assume a specific inference host, API provider, GPU platform, or model-serving framework. Qwen is the first evaluation target; Mistral, Gemma, and future open-weight families must plug into the same `ModelProvider` interface.

## Scoring architecture

- Category scores are first-class.
- Overall score is a weighted derivative only.
- Evaluator kinds remain separated:
  - objective
  - rule-based
  - human
  - llm-as-judge (advisory, never ground truth)

## What Phase 1 / 2A do not include

- Model weight downloads (Phase 2A intake is documentation + manifests only)
- Fine-tuning / LoRA training
- Live production inference
- Application UI or auth
- Cloud resource provisioning

Qwen intake documents live under `docs/QWEN_*.md` and `docs/decisions/ADR-0001-*.md`.

## Cloud-era architecture package (Phase 3G.5)

For post–Phase 3F workflows (qualification, cloud execution, evidence, cleanup, dependency pins), see **`docs/architecture/`**. Standing Phase 1 framing above remains valid for lab vs Investigator separation.
