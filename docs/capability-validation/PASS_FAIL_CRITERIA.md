# Pass / fail criteria — Phase 4 Capability Validation

Applies when execution is later authorized. Framework completeness is separate (see §5).

## 1. Task-level

| Result | Condition |
| --- | --- |
| **Pass+ / Pass** | Per `SCORING_RUBRIC.md` grade |
| **Marginal** | Usable only with heavy edit; counts against domain gates |
| **Fail** | Grade Fail or hard-fail override |

## 2. Domain-level gates

| Domain | Pass gate | Notes |
| --- | --- | --- |
| Code | ≥70% tasks Pass or Pass+; hard fails ≤1 | CG-10/11 Workers may be Marginal without failing domain if documented |
| Research | ≥75% Pass/Pass+; **zero** hard fails on RS-04…06 | Citation integrity is blocking |
| Investigator | ≥75% Pass/Pass+; **zero** hard fails on INV-05…08 | Contradiction + confidence blocking |
| Business | ≥65% Pass/Pass+; hard fails ≤1 | Lower bar; still no secret leakage |
| Reliability | REL-01 must be Pass/Pass+; ≥5/7 tasks Pass/Pass+; REL-04 must not hard-fail | Stability blocking |

A domain that misses its gate is **Domain Fail**.

## 3. Suite-level gates

| Suite result | Condition |
| --- | --- |
| **Suite Pass** | All five domains pass their gates; no U4 hard fails anywhere; env pins verified |
| **Suite Conditional Pass** | Suite would pass except Business and/or Workers-only Marginals; Research + Investigator + Reliability pass |
| **Suite Fail** | Research, Investigator, or Reliability domain fails; or any secret leakage; or pin drift detected |
| **Suite Invalid** | CobraBench executed; model/quant changed; or prompts iteratively gamed mid-run |

## 4. Blocking integrity checks (automatic Suite Invalid / Fail)

1. Runtime pins ≠ `phase-3f-qualified` equivalence (unless a new authorized runtime exists).
2. Official score text altered to a new number without a new official run.
3. Private/proprietary case data used as fixtures.
4. Mid-suite prompt rewriting to chase grades.
5. Missing cleanup after cloud execution (operational fail even if scores look good).

## 5. Framework deliverable pass (this phase)

Phase 4 **framework** passes if:

- [x] Validation plan exists
- [x] Task catalog covers all five domains and listed capabilities
- [x] Scoring rubric defined
- [x] Pass/fail criteria defined
- [x] Future automation plan exists
- [x] Capability matrix exists
- [x] No validation tasks executed in this phase

## 6. Reporting rules

- Never publish Phase 4 means as “CobraBench score.”
- Always state: official v0.1 = **0.840**; v0.2-rc2 = `prepared-not-run`.
- Always state runtime tag used.
- Usefulness labels must cite failing task IDs when not Production-ready assist.
