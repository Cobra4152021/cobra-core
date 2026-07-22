# Qwen3-8B Weakness Taxonomy (Phase 2E Part 3)

Static analysis taxonomy for assigning **primary** and **contributing** weakness causes on CobraBench v0.1 baseline cases. Every assignment must cite observable evidence from run artifacts (responses, meta JSON, rule checks, human scores) — not intuition alone.

## Classes

| Code | Name | Definition |
|------|------|------------|
| **M** | Model capability | Foundation-model reasoning, grounding, synthesis, or instruction-following limits not explained by runtime, caps, or scoring. |
| **R** | Runtime / quantization | 4-bit quality loss, offload, slowdown, numeric fidelity, or device-map effects. |
| **P** | Prompt / template | Unclear instructions, weak role framing, ambiguous delimiters, or chat-template interaction. |
| **L** | Output-length constraint | Truncation or compression caused by `max_new_tokens` (or equivalent) limiting completeness. |
| **B** | Benchmark defect | Ambiguous rubric, conflicting expectations, inadequate supplied evidence, or case design flaw. |
| **S** | Scoring / parser defect | False unsupported-claim flags, brittle keyword checks, exact-match strictness, citation-coverage miscalculation. |
| **H** | Human-review uncertainty | Reviewer subjectivity, borderline severity, unclear rationale, inconsistent dimension scoring. |
| **U** | Unknown | Insufficient evidence to assign any other class confidently. |

---

## M — Model capability

**Examples (Qwen3-8B baseline):**

- Shallow numeric contradiction explanation (`cb-019-metric-contradiction`).
- Missing explicit uncertainty in investigation responses (`cb-004`, `cb-005`, `cb-006`, `cb-008`).
- Incomplete email-thread grounding completeness (`cb-010-email-thread-grounding`).
- Wrong citation-key family (`[S2]` vs `SRC-A`) despite correct section content (`cb-024-long-policy-exceptions`).
- Partial coding task completion (`cb-021`, `cb-022`).

**Assignment rules:**

- Assign **M** as primary when the response text shows a reasoning or grounding gap that persists after accounting for token caps and parser false positives.
- Do **not** assign **M** when the answer is substantively correct but failed a keyword objective check — prefer **S** or **B**.

**Diagnostic test:** Thinking-mode cohort; prompt cohort with unchanged evidence; compare to strong control cases in the same category.

---

## R — Runtime / quantization

**Examples:**

- Suspected numeric imprecision under 4-bit NF4 (not directly observed in static review).
- Slow generation (~6.2 tok/s) causing practical pressure on long answers (indirect, not primary for v0.1 cases).

**Assignment rules:**

- Assign **R** only with runtime evidence (precision config, dtype, comparison run). Baseline static review has **no BF16 comparison** — default to contributing or **U**, not primary.
- Do not blame quantization for format or parser failures.

**Diagnostic test:** Future 8-bit/BF16 comparison on selected weak cases (out of scope for Phase 2E static gate).

---

## P — Prompt / template

**Examples:**

- Markdown bullets (`- **FINDING**:`) instead of exact `FINDING:` lines (`cb-027-exact-output-format`).
- Paragraph labels `(P2)` used where prompt expects `SRC-A` citation keys (`cb-023-long-memo-key-facts`).
- Ambiguous “cite section IDs” vs “cite citation keys” (`cb-024`).

**Assignment rules:**

- Assign **P** when the model follows a reasonable interpretation of ambiguous formatting instructions.
- Pair with **M** when the model ignores an unambiguous requirement.

**Diagnostic test:** Prompt-format cohort (original vs clarified vs schema-oriented).

---

## L — Output-length constraint

**Examples:**

- Responses at `output_token_count=512` with `max_new_tokens=512` (`cb-001`, `cb-002`, `cb-004`).
- Truncated late sections or missing citations **because** generation hit the cap.

**Assignment rules:**

- Assign **L** as primary only when `output_tokens` is at or near the cap **and** omitted content plausibly would appear after the cutoff.
- **Do not** assign **L** for `cb-023`/`cb-024` — both finished at ~127–128 tokens with `finish_reason=completed`.
- Near-cap alone is contributing, not primary, when the human score is high and content is complete.

**Diagnostic test:** Output-cap cohort (512 / 1024 / 2048) on long-document and verbose investigation cases.

---

## B — Benchmark defect

**Examples:**

- Rubric expects exact keywords (“pending”, “unconfirmed”) not stated in an otherwise correct answer (`cb-010`).
- Behavior checker keyword lists that fail valid responses (`cb-024` `pro-extra-exception` on the word “exceptions”).

**Assignment rules:**

- Assign **B** when case design or rubric ambiguity materially distorts objective/behavior scores.
- Often **contributes** alongside **M** or **S**, not replaces them.

**Diagnostic test:** Defect review + prospective v0.2 case revision (document only).

---

## S — Scoring / parser defect

**Examples:**

- 172 aggregate unsupported-claim flags vs 25/28 human H0 ratings.
- `cb-023` objective failure despite five numbered facts in the response.
- `cb-014` objective 0.0 despite correct URL non-invention.
- `cb-019` objective failure despite citing both metric values.

**Assignment rules:**

- Assign **S** as **contributing** whenever `unsupported_claim_count > 0` and `hallucination_severity_human == H0`.
- Assign **S** as **primary** when human review confirms quality but automated checks fail.

**Diagnostic test:** Unsupported-claim heuristic audit (`scripts/audit_unsupported_claims.py`); rule-check keyword review.

---

## H — Human-review uncertainty

**Examples:**

- Single reviewer, `evaluator_confidence=0.7` on all cases.
- Borderline H2 on `cb-013` with 0.85 overall score.

**Assignment rules:**

- Assign **H** when primary weakness depends on subjective severity or inconsistent dimension rationale.
- Use **contributing**, not primary, when automated and human scores align on the weakness.

**Diagnostic test:** Blinded rescoring consistency sample (≥8 cases).

---

## U — Unknown

**Examples:**

- Quantization impact without precision comparison data.
- Contradiction depth limit vs verbosity tradeoff on 512-token cap cases with high human scores.

**Assignment rules:**

- Use only when evidence is insufficient for any other class.
- Document what additional diagnostic would resolve ambiguity.

---

## Assignment procedure

For each case:

1. **Read** response text, `.meta.json` (`finish_reason`, token counts), rule failures, human rationale, citation metrics.
2. **Describe** `observed_weakness` in plain language (or `none material`).
3. Choose **one primary** class (or `none` / null when no material weakness).
4. Add **contributing** classes (0–3 typical).
5. Set **confidence**: `high` | `medium` | `low`.
6. List **evidence** as bullet strings referencing artifacts.
7. Name a **diagnostic test** from Phase 2E cohorts (or `none`).
8. Set **diagnostic priority** and **rerun_justified** only when a controlled variable is identified.

### Primary vs contributing

| Situation | Primary | Contributing |
|-----------|---------|--------------|
| Good answer, noisy heuristic | `none` | S |
| Correct facts, wrong cite key format | M or P | S |
| Keyword checker fail, good semantics | S | B |
| Truncated at 512 tokens, incomplete | L | M |
| High score, at token cap, complete | `none` | L, S |

### Confidence

- **High:** Response read + metrics align; no conflicting signals.
- **Medium:** Mixed signals (e.g., human 0.75, objective 0.0).
- **Low:** Borderline human severity or single-reviewer dependency.

---

## Related artifacts

- Case analysis JSON: `evaluations/analysis/qwen3-8b-v0.1-case-analysis.json`
- Builder: `scripts/build_phase2e_case_analysis.py`
- Schema: `src/cobra_core/analysis/weakness.py`

**Status:** Static review only — Built only until diagnostic reruns complete.
