# Defect Severity Guide

Use one severity per finding. When unsure between two levels, choose the higher severity and explain.

## D0 — No defect

No action needed.

**Example:** Case is clear, answerable, fair; rubric allows reasonable alternatives; evaluators fit the task.

## D1 — Documentation issue

Does not change case substance or scoring behavior.

**Example:** Typos in reviewer notes; unclear but non-blocking metadata; missing explanatory comment that does not alter expected behavior.

## D2 — Minor wording or scoring issue

Could cause limited inconsistency; does not invalidate the case.

**Example:** Slightly overstated difficulty label; generic human dimension text; shallow contradiction detector under-credits vague-but-correct wording (framework note).

## D3 — Material case or scoring defect

Could alter whether a good response passes or a poor response fails.

**Example:** Answer cue in a model-visible source title; mandatory citation scoring on a pure refusal task; vacuous objective checks that auto-pass empty substance; rubric treating one valid inference as the only allowed answer.

## D4 — Release-blocking defect

Case is unfair, unanswerable, contaminated, materially ambiguous, or process gates for final release are not met.

**Example:** Evidence does not contain facts needed to answer; gold answer embedded in the prompt; genuine second-reviewer independence required for finalization was not achieved (process D4).

## Mapping to case status

| Severity | Typical case status |
| --- | --- |
| D0 | approve |
| D1 | approve with note |
| D2 | approve with note or revise |
| D3 | revise (or remove if irreparable) |
| D4 | revise/remove; blocks final release |

Any D3/D4, revise, remove, or unresolved material ambiguity **blocks final v0.2** until addressed via a new RC or redesign outcome.
