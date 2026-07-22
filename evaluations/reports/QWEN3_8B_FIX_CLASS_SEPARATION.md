# Qwen3-8B Fix-Class Separation (Phase 2E Part 16)

Map material weaknesses to improvement classes. **Class 4 is not authorized** until Class 1–3 controls are tested and failures persist.

| Weakness | Fix class | Rationale |
| --- | --- | --- |
| W01 Unsupported-claim heuristic noise | **Class 3** — Evaluation framework | Version heuristic; do not train the model on false flags |
| W07 Behavior keyword false-fails | **Class 3** — Evaluation framework | Evaluator/rubric defect |
| W04 Exact FINDING format | **Class 2** (+ Class 3 parser policy) | Clarified prompt + dual semantic/exact scoring |
| W02 Long-doc citation keys P# vs SRC-A | **Class 2** (+ Class 3 rubric) | Prompt + accept secondary labels in v0.2 |
| W05 Investigation hits 512 cap | **Class 1** — Runtime | Higher cap / token budgeting |
| W06 Early stop on long-doc (~128 tok) | **Class 1/2 first**; Class 4 only if persists | Cap/prompt diagnostics blocked — not yet training-eligible |
| W03 Metric contradiction shallow | **Pending Class 1/2** (thinking + prompt); **maybe Class 4 later** | Needs reproducible persistence after controls |
| W08 Quantization unknown | **Class 1 / hardware** (not Class 4) | No BF16 A/B; impact Unknown |
| W09 GPU contention blocking diagnostics | **Class 1 / environment** | Free GPU; not a model defect |

## Class 4 eligibility gate (not met)

A weakness may enter Class 4 only when:

1. reproducible,
2. persists after reasonable prompt/runtime controls,
3. not primarily a benchmark defect,
4. material investigation risk.

**None of W03/W06 currently satisfy (2)** because Gate 6 diagnostics did not complete.

## Explicitly not training targets

- Format punctuation / markdown variants
- Heuristic false positives
- Keyword behavior-check mismatches
- Single-reviewer score noise within MAD ≈ 0.036
