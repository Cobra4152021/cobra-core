# CobraBench

CobraBench is the evaluation suite for Cobra Core candidate models.

## What it measures

| Category | Weight | Intent |
| --- | ---: | --- |
| Investigation reasoning | 20% | Structured investigative synthesis under uncertainty |
| Evidence grounding | 15% | Claims tied to provided sources |
| Hallucination resistance | 15% | Refusal to invent facts / people / documents |
| Citation correctness | 15% | Accurate citation keys and no fabricated sources |
| Contradiction detection | 10% | Explicit conflict identification without false resolution |
| Coding | 10% | Precise, testable coding assistance |
| Long-document analysis | 5% | Faithful long-context synthesis |
| Refusal quality | 5% | Appropriate, helpful refusals |
| Instruction following | 5% | Compliance with explicit constraints |

## Evidence types (kept separate)

1. **Objective measurements** — latency, token counts, deterministic string/regex checks.
2. **Rule-based checks** — programmatic comparison to expected/prohibited behaviors.
3. **Human evaluator judgments** — expert review with rationale.
4. **LLM-as-judge results** — advisory only; never unquestionable ground truth.

## Preservation requirements

Every evaluation must retain:

- exact prompt (system + user)
- exact model revision
- inference parameters
- raw model output (path/location)
- evaluator version
- scoring rationale
- category-level scores (not only overall)

## Initial synthetic cases

See `benchmarks/cases/`:

- A. Evidence-grounded investigation (`cb-001-...`)
- B. Contradictory witness statements (`cb-002-...`)
- C. Citation and unsupported-claim detection (`cb-003-...`)

All cases are synthetic and public-safe.
