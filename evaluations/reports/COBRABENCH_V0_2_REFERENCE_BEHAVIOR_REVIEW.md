# CobraBench v0.2 Reference-Behavior Challenge Review

**Phase:** 2H  
**Scope:** All 46 rc1 cases (behavior challenged before rc2 patching)

## Method

For each case, expected behaviors, prohibited behaviors, and `reference_behavior` were challenged for:

* multiple valid conclusions,
* inference treated as fact,
* over-narrow prohibited behaviors,
* citation alternatives,
* confidence band reasonableness,
* omission severity,
* unfair penalty to cautious answers.

Original Phase 2G approval notes were not used as authority.

## Findings

### Valid alternative answers (acceptable)

| Case | Note |
| --- | --- |
| cb2-003 | Multiple failure hypotheses equally preservable; ordering of next steps may vary |
| cb2-006 | Next-step priority can reasonably differ if still evidence-seeking |
| cb2-009 | Offline causes may be listed in different groupings |
| cb2-027 | May say “apparent conflict resolved by timezone” or “no material contradiction” |
| cb2-044 / cb2-046 | Confidence language bands allow multiple phrasings |

### Overly narrow expected behavior (rc1)

| Case | Issue | rc2 action |
| --- | --- | --- |
| cb2-037–039 | Implicit expectation of citations via evaluator pins | Dropped mandatory citation evaluator |
| cb2-041 | Tolerant recovery allowed while JSON-only strict | `tolerant_recovery_allowed=false` |
| Several grounding titles | Title stated the conclusion type | Titles neutralized |

### Underdefined uncertainty

| Case | Issue |
| --- | --- |
| cb2-008 | Acceptable “incomplete” language is broad; human scoring needed |
| cb2-028 | Distinguishing uncertainty vs contradiction is mostly human-judged |

### Rubric–answer mismatch risks

* Objective checks in rc1 were nearly vacuous (`contains_any` non-empty) → keyword-pass risk for poor answers (**D2H-001**, D3).
* Reference wording must not control scoring; rc1/rc2 rubrics state wording similarity is not required.

### Cases where reference wording must not control scoring

All 46 cases. Scoring remains behavior-based plus evaluator metrics; no canonical prose match.

## Conclusion

No case was judged unanswerable. Several expected-behavior and evaluator couplings were too narrow or unfair; corrected in **rc2** under Outcome B.
