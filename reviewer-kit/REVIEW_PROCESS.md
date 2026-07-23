# Review Process (Blind-First)

## Independence

Record your identity, affiliation, and whether you authored cases or performed a prior review of this RC.

Preferred: you did **not** author the cases and did **not** perform the immediately prior review.

## Blind answerability pass (mandatory)

For each case, open **only**:

* `user_prompt` / task instructions,
* `system_prompt` if shown as model-facing,
* `supporting_sources` (evidence),
* output / format constraints,
* runtime or output-budget notes if present.

**Do not** open yet:

* `expected_behaviors`,
* `prohibited_behaviors`,
* `reference_behavior`,
* scoring rationale notes that reveal the intended answer,
* prior review approval notes.

### Blind questions (record before rubric)

1. Is the central task understandable?
2. Is the case **answerable** from supplied evidence?
3. Is outside knowledge required?
4. What ambiguity exists?
5. What plausible conclusions exist?
6. What uncertainty is necessary?
7. Which evidence appears material?
8. Is there an apparent contradiction?
9. Approximate output length needed?
10. Fairness (reasoning demand vs confusing wording)?
11. Initial difficulty estimate (1–5)?
12. Confidence in your blind judgment (low/medium/high)?

Blind status (pick one):

* answerable
* answerable with uncertainty
* ambiguous but usable
* materially ambiguous
* unanswerable

**Save the blind form** before revealing the rubric.

## Rubric comparison pass

Only after blind notes are saved, compare against:

* expected / prohibited behaviors,
* material / optional / contrary evidence IDs,
* semantic vs exact-format requirements,
* evaluator pins,
* human-scored dimensions.

Record agreement, acceptable alternatives, or rubric defects (too narrow/broad, unsupported expectations, evaluator mismatch).

## Case decision

Use `CASE_REVIEW_FORM.md` and `DEFECT_GUIDE.md`.

Statuses:

* approve
* approve with note
* revise
* remove

Unresolved material ambiguity cannot enter a final release.

## Suite completion

Complete `SUMMARY_REPORT_TEMPLATE.md` with Outcome A/B/C/D recommendation.
