# Qwen3-8B Format Compliance Audit

**Run ID:** `20260722T200000Z-8bba5e01`  
**Focus cases:** `cb-027-exact-output-format`, `cb-028-json-only-response`  
**Category score:** 0.850  
**Scope:** Static inspection only.

## cb-027 — Exact output format

### Requirement (case file)

> Answer using exactly three bullets labeled FINDING, RISK, NEXT. No other sections.

### Actual response

```
- **FINDING**: The synthetic scanner identified one outdated dependency in the demo application.  
- **RISK**: Outdated dependencies may introduce security vulnerabilities or compatibility issues.  
- **NEXT**: Review the specific dependency for known vulnerabilities and update it to a supported version.
```

### Automated checks

| Check | Result |
|-------|--------|
| `obj-labels-present` (FINDING, RISK, NEXT) | **Pass** |
| `exp-three-labels` | **Pass** |
| `pro-extra-sections` | **Pass** |
| Objective score | 1.0 |
| Behavior score | 1.0 |

### Human review

- **Score:** 0.70
- **Rationale:** “Used markdown bullets instead of exact FINDING/RISK/NEXT lines; content otherwise aligned.”

### Failure classification

| Aspect | Class | Notes |
|--------|-------|-------|
| Semantic content | **Correct** | Finding/risk/next all grounded in SRC-A scan summary |
| Syntactic format | **Partial miss** | Markdown `- **LABEL**:` vs exact `FINDING:` prefix lines |
| Parser/objective | **Pass** | Keyword checker too lenient vs human dimension |
| Ambiguous requirement | **Yes** | “Exactly three bullets labeled FINDING, RISK, NEXT” does not forbid markdown |
| Harmless variation | **Debatable** | Fine for human readers; problematic for strict machine parsers |

**Primary cause:** **P** (prompt ambiguity) with **S** contributing (objective pass vs human format dimension divergence).

**Not** a material semantic instruction-following failure.

---

## cb-028 — JSON-only response (control: pass)

- Valid JSON body; required keys present.
- **Human:** 1.0 | **Objective:** 1.0
- **Classification:** none — true compliance.

---

## Other instruction-adjacent cases

| Case | Format note |
|------|-------------|
| cb-023 | Numbered list + markdown bold — acceptable for task, hurts SRC-A citation |
| cb-002 | Markdown headings — not an instruction-following case |
| cb-020–022 | Code fence conventions — coding category |

No other instruction_following cases in v0.1 beyond cb-027/cb-028.

---

## Audit summary

| Failure type | cb-027 | cb-028 |
|--------------|--------|--------|
| Semantic failure | No | No |
| Syntactic failure | Partial (markdown vs exact lines) | No |
| Parser failure | Objective too lenient vs human | No |
| Ambiguous requirement | Yes | No |
| Harmless variation | Arguable | N/A |
| True IF failure | No | No |

## Recommendations

1. **Clarify cb-027 prompt** with an example line: `FINDING: …` (no markdown).
2. **Align objective checks** with human format dimension (regex for line-anchored labels).
3. **Prompt-format diagnostic cohort** before attributing to model noncompliance.
4. Do **not** penalize cb-027 at full semantic penalty — content was correct.

**Status:** Static review only.
