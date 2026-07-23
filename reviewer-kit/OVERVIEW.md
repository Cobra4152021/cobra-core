# CobraBench Overview for External Reviewers

## What you are reviewing

Typically: **CobraBench v0.2-rc2** — a frozen, non-final release candidate with 46 synthetic cases.

You are **not** asked to re-score Qwen3-8B or to change the official v0.1 baseline.

## Official vs release candidate

| Item | Role |
| --- | --- |
| CobraBench v0.1 | Official benchmark; Phase 2D official interim score **0.840** |
| v0.2-rc1 | Immutable prior RC |
| v0.2-rc2 | Current RC under governance freeze (Milestone M1) |
| Final v0.2 | **Not released** (Phase 2I Outcome D) |

## Evidence-first reasoning

Models must answer from supplied SOURCE blocks. Outside knowledge is not required and inventing facts is a failure mode.

## Fact versus inference

* **Fact:** directly supported by evidence (cite sources).
* **Inference:** labeled as inference; must not be overstated as established fact.
* **Unknown:** explicit when evidence is incomplete.

## Citation expectations (v0.2)

* Use keys such as `[S1]`.
* Citation precision and evidence coverage both matter.
* A fully cited answer can still fail if material evidence is omitted.
* Contrary evidence should be preserved/cited when material.

## Contradiction handling

Score dimensions include detection, localization, explanation, numerical/timeline comparison, preservation of competing accounts, avoidance of invented reconciliation, resolution-evidence recommendations, and confidence calibration.

Apparent contradictions that resolve with context must not be forced into “true contradiction.”

## Semantic versus exact-format scoring

* **Semantic:** required fields/meaning present.
* **Exact-format:** syntax/parseability when the case requires it.
* Harmless markdown variation is not automatically a semantic failure.
* JSON-only / machine-interoperability cases may require strict parsing.

## Governance (how versions work)

1. **New benchmark version:** author cases → validate → review → freeze new release directory with new ID.
2. **Evaluator freeze:** pin semantic versions under `evaluators/`; never silently edit a frozen pin’s meaning.
3. **RC promotion:** only after documented review outcomes (A/B/C/D); final release needs genuine independence gates.
4. **Hashes:** SHA-256 per case file in `INVENTORY.json`; tree hash over release files (excluding `SHA256SUMS` / `TREE_HASH.txt` as documented).
5. **Inventory freeze:** case list + content hashes must match disk.
6. **Historical scores:** remain tied to the benchmark + evaluator + protocol versions used; never rewritten in place.

See also `docs/EVALUATION_POLICY.md` and `docs/milestones/M1_Benchmark_Freeze.md`.
