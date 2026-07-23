# CobraBench External Reviewer Kit

**Audience:** Independent reviewers who have not followed the full Phase 2 history  
**Milestone:** M1  
**Benchmark under review (typical):** CobraBench v0.2-rc2 (non-final release candidate)  
**Official benchmark (do not confuse):** CobraBench v0.1

## Purpose of CobraBench

CobraBench evaluates whether an AI system can perform **evidence-first investigation work** accurately, transparently, cautiously, and usefully.

It prioritizes:

* evidence grounding,
* claim-to-source traceability,
* contradiction handling,
* fact-versus-inference separation,
* uncertainty calibration,
* hallucination resistance,
* missing-information recognition,
* proportional recommendations,
* structured output reliability,
* investigation usefulness.

It does **not** primarily reward verbosity, polished prose, broad world knowledge, unsupported creativity, confident guessing, or stylistic similarity to a reference answer.

## Start here

1. Read `OVERVIEW.md`
2. Read `REVIEW_PROCESS.md` (includes **blind review** rules)
3. Use `REVIEW_CHECKLIST.md` and `CASE_REVIEW_FORM.md` per case
4. Classify issues with `DEFECT_GUIDE.md`
5. Ask clarifying questions via `QUESTION_TEMPLATE.md`
6. Deliver results with `SUMMARY_REPORT_TEMPLATE.md`

## Repository layout (what you need)

| Path | Role |
| --- | --- |
| `benchmarks/releases/cobrabench-v0.1/` | **Official** frozen benchmark |
| `benchmarks/releases/cobrabench-v0.2-rc2/` | Current non-final release candidate (typical review target) |
| `benchmarks/releases/cobrabench-v0.2-rc1/` | Prior immutable RC (historical) |
| `evaluators/` | Versioned evaluator metadata |
| `prompts/` | Versioned prompt templates |
| `runtime_policies/` | Versioned runtime profiles |
| `docs/EVALUATION_POLICY.md` | Score and immutability rules |
| `docs/milestones/M1_Benchmark_Freeze.md` | Frozen milestone status |

## Benchmark philosophy (short)

* All necessary facts must be in the supplied evidence.
* Facts and inferences must be separable.
* Citations use source keys (v0.2: `S1`, `S2`, …).
* Contradictions must be preserved, not invented away.
* Semantic compliance ≠ exact-format compliance.
* Deterministic evaluators are **partial proxies**; human judgment still matters.

## Known evaluator limitations

* Unsupported-claim v2 may mark novel claims `cannot_determine` instead of unsupported (high false-negative risk on adversarial fixtures).
* Contradiction v2 under-scores shallow but correct detection wording.
* Objective checks are incomplete; do not treat automated pass as full quality.
* Refusal and uncertainty categories are small-sample (n=3 each on v0.2 RCs).

## Expected review duration

| Activity | Estimate |
| --- | --- |
| Kit + overview reading | 45–90 minutes |
| Per case (blind + rubric) | 8–15 minutes |
| Full 46-case rc2 pass | ~8–12 hours across sessions |
| Summary report | 1–2 hours |

Do not rush the blind pass.

## Required reviewer qualifications

* Comfortable with evidence-based investigation or intelligence/analysis writing
* Able to separate fact, inference, and speculation
* Willing to follow blind-before-rubric discipline
* Not an author of the cases under review
* Ideally did not perform the immediately prior review of the same RC

## Important status notes

* Official score **0.840** is CobraBench **v0.1** only.
* rc1/rc2 do **not** supersede v0.1.
* No model should be run as part of this review kit usage.
* Do not designate any model as Cobra Core.
