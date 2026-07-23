# ADR-0009 — Review Governance and Milestone M1

- **Status:** Accepted
- **Date:** 2026-07-23
- **Phase:** 3A

## Context

Phases 2D–2I completed official v0.1 baselining and v0.2 release-candidate engineering. Phase 2I selected Outcome D: rc2 remains non-final because genuine second-reviewer separation was not achieved. The project needs durable governance artifacts so external reviewers can evaluate RCs without historical chat context.

## Decision

1. Freeze documentation of completed work as **Milestone M1**.
2. Publish an external **reviewer kit** with mandatory blind-before-rubric process.
3. Codify evaluation policy: official scores immutable; RCs experimental; versions frozen by hash.
4. Keep model evaluation and Cobra Core designation **out of scope** for M1.

## Reasons

### Why Milestone M1 exists

To mark a clean boundary between benchmark engineering and later model evaluation campaigns, with frozen hashes and ADRs as the source of truth.

### Why reviewer kits exist

External reviewers should not need the Phase 2 chat history. The kit carries philosophy, process, forms, defect severities, and outcome definitions.

### Why blind review is required

Seeing expected behaviors first biases answerability judgments and hides cases that are unfair or unanswerable. Blind pass first, rubric second.

### Why release candidates are frozen

In-place edits destroy reproducibility. Corrections require a new RC ID and new hashes.

### Why official benchmarks remain immutable

The Phase 2D **0.840** result is meaningful only under CobraBench v0.1 + its original pins. Rewriting it would erase the historical baseline.

### Why model evaluations remain separate from benchmark engineering

Mixing authoring/review with scoring a candidate model conflates benchmark quality with model quality and risks motivated scoring changes.

## Consequences

* Phase 3A adds docs and `reviewer-kit/` only.
* No case, evaluator, prompt, or runtime profile content changes.
* Final v0.2 still requires a genuine independent second reviewer (or justified Outcome B/C path).
* No Cobra Core designation.

## Related

* `docs/milestones/M1_Benchmark_Freeze.md`
* `docs/EVALUATION_POLICY.md`
* `docs/ROADMAP.md`
* `reviewer-kit/`
* ADR-0008 (Outcome D)
