# Qwen3-8B Long-Document Diagnostic

**Run ID:** `20260722T200000Z-8bba5e01`  
**Cases:** `cb-023-long-memo-key-facts`, `cb-024-long-policy-exceptions`  
**Scope:** Static inspection only — no new inference.

## Protocol context

- `max_new_tokens`: **512**
- Category score (interim): **0.725**
- Both cases use a single embedded long source in `SRC-A` (synthetic memo / policy excerpt).

## Token and finish metadata

| Case | Input tokens | Output tokens | Finish reason | At 512 cap? |
|------|-------------|---------------|---------------|-------------|
| cb-023 | 213 | **127** | `completed` | **No** |
| cb-024 | 173 | **128** | `completed` | **No** |

**Finding:** Neither long-document response was truncated by the output token limit. Weakness is **not** primarily **L** (output-length constraint) for these two cases.

Cases elsewhere (`cb-001`, `cb-002`, `cb-004`) did reach **512** output tokens; those are investigation/evidence categories, not long-document cases.

## cb-023 — Long memo key facts

### Response summary

Five numbered facts covering M1–M3 milestones, budget cap, and staffing risk. Paragraph labels `(P2)`–`(P7)` are used correctly for memo content.

### Objective / behavior scores

- Objective: **0.0** (failed `obj-paragraph-ref` regex — checker expected word “references”, not `P2` pattern)
- Behavior: **0.333** (keyword checker missed “five facts” despite five list items)
- Human: **0.75** — “Captured key milestones/budget/risk; some formatting verbosity.”

### Weakness decomposition

| Capability | Assessment |
|------------|------------|
| Extraction | **Adequate** — five relevant facts present |
| Prioritization | Acceptable — omitted P1 (no production) and P6 (publish date) |
| Citation discipline | **Weak** — no `SRC-A` keys; uses inline `P#` only → `citation_coverage=0` |
| Truncation | **Not observed** — 127/512 tokens used |
| Scoring | **Material distortion** — objective/behavior failures appear brittle |

**Primary cause:** **S** (scoring/parser) with **M** (citation key habit) and **P** (ambiguous “paragraph labels” vs SRC-A keys) contributing.

### Diagnostic recommendation

- Cohort A: rerun with 1024 cap (control — expect similar content length).
- Cohort C/D: prompt clarifying `SRC-A` citation keys alongside paragraph labels.

## cb-024 — Long policy exceptions

### Response summary

Lists exceptions E1–E3 with correct retention details. Uses inline `[S2]`–`[S5]` bracket cites, not `SRC-A`.

### Objective / behavior scores

- Objective: **1.0** (matched “exception” keyword)
- Behavior: **0.0** (keyword checker failed “Lists … section citations”; false prohibited hit on “exceptions”)
- Human: **0.70** — partial completeness wording

### Weakness decomposition

| Capability | Assessment |
|------------|------------|
| Exception identification | **Strong** — E1, E2, E3 all present |
| Citation format | **Wrong key family** — section IDs instead of `SRC-A` |
| Truncation | **Not observed** — 128/512 tokens |
| Scoring | Behavior checker **false negatives/positives** |

**Primary cause:** **M** (citation key discipline) with **S** and **P** contributing.

### Diagnostic recommendation

- Cohort D: explicit delimiter block + “cite using SRC-A only” instruction.
- Do **not** conclude long-context failure from these responses.

## Conclusion

Long-document category weakness on this baseline reflects:

1. **Citation key confusion** (section/paragraph IDs vs `SRC-A`) — model/prompt (**M**, **P**).
2. **Brittle rule-based scoring** inflating apparent failure (**S**).
3. **Not** output-cap truncation for cb-023/cb-024.

A controlled output-cap rerun remains justified for **confirming** that 512 tokens is sufficient for these cases (expect null effect).

**Status:** Static review only — Not verified by diagnostic reruns.
