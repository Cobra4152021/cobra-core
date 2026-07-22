# CobraBench v0.1 — Frozen Release

This directory is the **authoritative frozen snapshot** of CobraBench v0.1.

**Release date:** 2026-07-22  
**Evaluator bundle:** `cobrabench-evaluator-v0.1.0`  
**Case count:** 28

## Contents

| File / directory | Purpose |
|------------------|---------|
| `RELEASE.md` | Release notes (this file) |
| `metadata.json` | Release identity and case counts |
| `weights.json` | Scoring weights for `cobrabench_weighted_v1` |
| `cases/` | 28 synthetic benchmark case JSON files |
| `INVENTORY.json` | Deterministic file list + SHA-256 content hashes |

## Versioning

- **Release slug:** `cobrabench-v0.1`
- **Case schema version:** `0.1.0` (per-case `version` field)
- **Rubric:** `cobrabench_weighted_v1` / `1.0.0`
- **Inventory:** `INVENTORY.json` (SHA-256 per case file) — regenerate only when intentionally cutting a new release

## Scoring weights

| Category | Weight |
| --- | ---: |
| investigation_reasoning | 0.20 |
| evidence_grounding | 0.15 |
| hallucination_resistance | 0.15 |
| citation_correctness | 0.15 |
| contradiction_detection | 0.10 |
| coding | 0.10 |
| long_document_analysis | 0.05 |
| refusal_quality | 0.05 |
| instruction_following | 0.05 |

Weights sum to 1.0. Category detail is always retained.

## Known limitations

- Small synthetic suite; not a public leaderboard substitute.
- Heuristic rule checks are assistive, not ground truth.
- Human review is required for failures and a ≥25% sample of outputs.
- LLM-as-judge is advisory only.

## Prohibited uses

- Do not use active investigations, private evidence, or PII.
- Do not train on held-out CobraBench cases.
- Do not publish full prompts prematurely (contamination risk).
- Do not treat a single weighted overall as a “winner” declaration for Cobra Core.

## Change-control policy

Once evaluation against v0.1 begins, do **not** alter v0.1 cases or rubrics. Corrections require a new benchmark version (e.g. v0.2) with a new inventory.

## Category distribution (28 cases)

| Category | Count |
|----------|------:|
| investigation_reasoning | 4 |
| evidence_grounding | 4 |
| hallucination_resistance | 4 |
| citation_correctness | 4 |
| contradiction_detection | 3 |
| coding | 3 |
| long_document_analysis | 2 |
| refusal_quality | 2 |
| instruction_following | 2 |

## Working copies

Identical case files are mirrored under `benchmarks/cases/` for day-to-day validation and development. **This release directory is authoritative** for evaluation comparisons and inventory verification.

## Regenerating inventory

After any intentional change to frozen cases (which should be rare — prefer a new release version):

```bash
python scripts/build_cobrabench_inventory.py --version 0.1
```

## Verification

```python
from cobra_core.benchmarks.release import load_release_cases, validate_release_inventory

cases = load_release_cases("0.1")
assert not validate_release_inventory("0.1")
```

See also: `docs/COBRABENCH_CONTAMINATION_POLICY.md`.
