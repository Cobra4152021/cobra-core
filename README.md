# Cobra Core — Model Lab

Evidence-first open AI model research lab for investigation, research, source analysis, contradiction detection, citation discipline, and hallucination resistance.

> **This repository is not Cobra Investigator.**  
> No application UI, authentication, billing, investigation case management, Evidence Vault, or production chat endpoints live here.

## Mission

Build the research, benchmarking, evaluation, and future training foundation for **Cobra Core** — a model family optimized for investigative rigor rather than unconstrained fluency.

## Separation from Cobra Investigator

| | Cobra Core (this repo) | Cobra Investigator |
| --- | --- | --- |
| Role | Model lab | Product application |
| Benchmarks / manifests / evals | Yes | No |
| User-facing investigation workflows | No | Yes |
| Auth / billing / Evidence Vault | No | Yes |

## What Cobra Model Lab does

- Model intake via typed `ModelManifest` records
- CobraBench case design and validation
- Evaluation run preservation (prompts, revisions, raw outputs, rationales)
- Provider-neutral interfaces for Qwen, Mistral, Gemma, and future open-weight models
- Guardrails that block fine-tuning before baseline evaluation

## What CobraBench measures

Weighted categories (category detail is always retained):

| Category | Weight |
| --- | ---: |
| Investigation reasoning | 20% |
| Evidence grounding | 15% |
| Hallucination resistance | 15% |
| Citation correctness | 15% |
| Contradiction detection | 10% |
| Coding | 10% |
| Long-document analysis | 5% |
| Refusal quality | 5% |
| Instruction following | 5% |

Scores separate **objective**, **rule-based**, **human**, and **LLM-as-judge** evidence. LLM-as-judge is advisory only — never unquestionable ground truth.

## Why no fine-tuning before baseline evaluation

Fine-tuning without a measured baseline hides regressions and invents progress. Cobra Core requires:

1. Exact model intake
2. Baseline CobraBench scores with preserved artifacts
3. Comparative and weakness analysis
4. Dataset design informed by failures

Only then is LoRA / adapter work justified.

## Planned progression

1. **Phase 1** — Model intake and baseline benchmarking foundation *(complete)*
2. **Phase 2A–2E** — Qwen intake, 8B baseline, static weakness analysis *(complete; live 2E diagnostics deferred)*
3. **Phase 2F** — Prompt, runtime, parser, and evaluator improvements *(framework only; no model load)*
4. **Later** — Live diagnostics / optional CobraBench v0.2 release / dataset design only with separate authorization

### Phase 2F notes

- Evaluator v2 does **not** replace the official CobraBench v0.1 baseline score (**0.840**).
- CobraBench v0.2 is **draft schema only** — not released.
- Live Phase 2E diagnostics remain deferred.
- No training is authorized.
- See `docs/decisions/ADR-0005-prompt-runtime-evaluator-improvements.md`.

### Current Qwen status (lab)

| Role | Model | Status |
| --- | --- | --- |
| Primary baseline candidate | Qwen3-32B | acquired; local load blocked on this host |
| Development / interim baseline | Qwen3-8B | interim CobraBench v0.1 complete; **not** Cobra Core |
| Reasoning challenger | Qwen3-30B-A3B-Thinking-2507 | not acquired |

This does **not** designate any model as Cobra Core.

## Requirements

- Python **3.12+**
- No model weights in this repo
- No public software license yet (private / unlicensed for distribution)

## Setup

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Unix:
# source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Commands

| Task | Command |
| --- | --- |
| Validate benchmark cases | `python scripts/validate_cases.py` or `cobra-validate-cases` |
| Validate model manifests | `python scripts/validate_manifests.py` or `cobra-validate-manifests` |
| Unit tests | `python scripts/run_tests.py` or `pytest` |
| Lint | `python scripts/run_lint.py` or `ruff check src tests scripts` |
| Format check | `python scripts/run_format_check.py` or `ruff format --check src tests scripts` |
| Type check | `python scripts/run_typecheck.py` or `mypy src/cobra_core` |
| Empty eval report template | `python scripts/report_template.py` or `cobra-report-template` |
| All quality gates | `python scripts/run_quality.py` |
| Preflight environment | `python scripts/preflight_environment.py` |
| Acquire pinned model | `python scripts/acquire_model.py --manifest model-cards/qwen/qwen3-8b.manifest.json` |
| Verify hashes | `python scripts/verify_model.py --manifest model-cards/qwen/qwen3-8b.manifest.json` |
| Smoke tests (model required) | `python scripts/run_smoke_tests.py` |

Weights are stored outside git under `COBRA_MODEL_HOME` (default `D:\cobra-models`). See `docs/MODEL_STORAGE.md` and `docs/LOCAL_INFERENCE.md`.

## Repository map

```
benchmarks/cases/      Synthetic CobraBench cases
benchmarks/rubrics/    Weighted scoring config
benchmarks/schemas/    JSON Schema documents
datasets/              Dataset roots (contents mostly gitignored)
evaluations/           Results/reports roots + template
inference/             Inference stub notes
model-cards/           ModelManifest examples/records
providers/             Provider notes (Qwen first)
training/              Non-operational Phase 1 guards
adapters/              Future adapter metadata home
scripts/               Validation & quality scripts
src/cobra_core/        Installable package
tests/                 Unit tests
docs/                  Architecture, CobraBench, intake, security
```

## Definition of Done — Phase 1

- [x] Repository structure exists
- [x] Python project installs successfully
- [x] Tests pass
- [x] Linting passes
- [x] Type checking passes
- [x] Schemas validate correct examples
- [x] Schemas reject malformed examples
- [x] Three synthetic CobraBench cases exist
- [x] No model weights have been downloaded
- [x] No training code is operational
- [x] No secrets or private evidence are committed
- [x] Documentation clearly separates Cobra Core from Cobra Investigator

## License

No public software license has been added yet.
