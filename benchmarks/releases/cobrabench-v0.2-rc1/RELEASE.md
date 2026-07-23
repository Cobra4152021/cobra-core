# CobraBench v0.2-rc1

> Release candidate — not final.

## Identity

- Release ID: `cobrabench-v0.2-rc1`
- Case count: **46**
- Final release: **false**
- Inventory case hash count: **46**
- Tree hash: see `TREE_HASH.txt` (hashes all release files except `SHA256SUMS` and `TREE_HASH.txt`)

## Category distribution

| Category | Count |
| --- | ---: |
| citation_correctness | 5 |
| coding | 4 |
| contradiction_detection | 6 |
| evidence_grounding | 6 |
| hallucination_resistance | 5 |
| instruction_following | 4 |
| investigation_reasoning | 6 |
| long_document_analysis | 4 |
| refusal_quality | 3 |
| uncertainty_calibration | 3 |

## Difficulty distribution

| Level | Count |
| --- | ---: |
| 1 | 8 |
| 2 | 21 |
| 3 | 12 |
| 4 | 5 |

## Weights

See `weights.json` (`cobrabench_weighted_v2_rc1`). Total 100%.

## Evaluator versions

- unsupported_claims 2.0.0
- citations 2.0.0
- contradictions 2.0.0
- format_compliance 2.0.0
- output_budget_telemetry 1.0.0

## Prompt templates / runtime profiles

Referenced from `prompts/` and `runtime_policies/` registries (v2 evidence standard).

## Review status

- Human static review: single-reviewer, 100% approved
- Unresolved material ambiguities: 0
- Contamination review: see `docs/COBRABENCH_V0_2_CONTAMINATION_REVIEW.md`

## Known limitations

- Not executed against any model in Phase 2G
- Deterministic evaluators remain incomplete proxies for judgment
- Scores are not comparable to CobraBench v0.1 / 0.840
- Single-reviewer process (not multi-rater)

## Incompatibility with v0.1

Do not present rc1 scores as direct improvement or decline versus 0.840.
