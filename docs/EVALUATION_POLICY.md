# Cobra Evaluation Policy

**Status:** Active  
**Milestone:** M1  
**Date:** 2026-07-23

## Core rules

1. **Official scores never change** after freeze without a new benchmark version and new evaluation run.
2. **Release candidates are experimental** and do not replace official benchmarks.
3. **Benchmark releases are immutable** after freeze (cases, inventory, tree hashes).
4. **Evaluator versions are versioned**; do not silently edit a pinned version in place.
5. **Prompt-template versions are versioned**.
6. **Runtime profiles are versioned**.
7. **Historical reports remain reproducible** from frozen hashes and protocol pins.
8. **No cross-version score comparisons** without explicit qualification (no conversion formulas without statistical support).

## Official versus experimental

| Kind | Example | Reporting rule |
| --- | --- | --- |
| Official | CobraBench v0.1 + Phase 2D 0.840 | May be cited as official interim baseline |
| Release candidate | v0.2-rc1, v0.2-rc2 | Label non-final; not interchangeable with 0.840 |
| Diagnostic | Phase 2E deferred runs | Separate run IDs; never overwrite locked baseline dirs |

## Version immutability

When a release is frozen:

* case JSON content is fixed,
* `INVENTORY.json` case hashes are fixed,
* `TREE_HASH.txt` / `SHA256SUMS` are fixed,
* corrections require a **new** release ID (rcN+1 or final), never in-place edits.

## Evaluator / prompt / runtime pins

* Cases and protocols must pin explicit versions.
* Improving an evaluator creates a new version (e.g. 2.1.0), leaving prior versions intact.
* Changing pins changes score compatibility and must be documented.

## Human review

* Blind answerability before rubric consultation is required for release-candidate and final reviews.
* Single-reviewer processes must be labeled as such.
* Genuine second-reviewer separation is required before final CobraBench v0.2 promotion (see ADR-0008 / ADR-0009).

## Model evaluation separation

Benchmark engineering (authoring, review, freeze) is separate from model evaluation.

* Do not execute model protocols during documentation/governance phases.
* Do not designate **Cobra Core** from benchmark engineering alone.

## Prohibited reporting practices

* Presenting rc2 scores as “improvement over 0.840” without qualification
* Editing locked baseline result inventories
* Claiming multi-rater review when only one workflow reviewed
* Claiming production readiness without evidence labels from the engineering skill
