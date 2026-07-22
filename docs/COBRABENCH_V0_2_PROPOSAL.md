# CobraBench v0.2 Proposal (Prospective)

**Date:** 2026-07-22  
**Source:** Phase 2D defect review + Phase 2E static analysis  
**Status:** Proposal only — **do not modify CobraBench v0.1**; **do not create an official v0.2 release in Phase 2E closure**.

| # | Limitation | Evidence | Proposed correction | Scores comparable to v0.1? | Migration |
| --- | --- | --- | --- | --- | --- |
| 1 | Unsupported-claim heuristic noise | Audit precision ≈0% on 50 flags | **Versioned** unsupported-claim heuristic with measured precision gates before official use | No if changed silently | Keep v0.1 scores; publish evaluator notes |
| 2 | No heuristic quality bar | Aggregate 172 treated as signal | Require measured precision / FPR reporting before totals enter official dashboards | Diagnostic-only until met | Separate diagnostic score stream |
| 3 | Exact-format vs semantic conflation | cb-027 markdown bullets | Dual scores: semantic sections + exact machine format | Partial | New metrics in v0.2 |
| 4 | Contradiction dimensions conflated | cb-019 vs cb-018 | Separate submetrics: detection / explanation / resolution-evidence | No (redefined category) | New rubric dimensions |
| 5 | Citation-coverage measurement gaps | Precision 1.0 with incomplete coverage | Improve coverage measurement; accept documented secondary keys where prompted | Partial | Clarified coverage rules |
| 6 | Keyword behavior checkers | Strong human vs failed keywords | Review/demote brittle keyword checkers | Improves fairness | RELEASE notes |
| 7 | Long-document suite small | n=2 | Add long-document cases | Broader coverage | Additive cases only |
| 8 | Early-stop vs truncation ambiguity | cb-023/024 completed ≪512 | Explicit early-stop analysis fields (finish_reason, tokens used vs cap) | Protocol enrichment | Diagnostics + v0.2 case fields |
| 9 | Uncertainty calibration under-tested | Mixed overstatement heuristics | Dedicated uncertainty-calibration cases | Additive | New cases |
| 10 | Frozen result-directory protection | Phase 2E wrote into locked run once | Immutable baseline locks + refuse analysis writes into locked trees | Process | Locks + tests |
| 11 | Diagnostic vs official conflation risk | Cohort suite defined | Hard separation: diagnostics never called CobraBench v0.1; new run IDs | N/A | Suite + ADR policy |

## Comparability statement

Any v0.2 change that alters rubrics, parsers, or case text **breaks direct score comparability** with v0.1. Report side-by-side with version labels. Never silently rescore the frozen Phase 2D baseline.
