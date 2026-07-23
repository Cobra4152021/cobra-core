# CobraBench v0.2 Scoring Design

**Status:** Release-candidate design for v0.2-rc1  
**Weights total:** 100%

Weights were chosen for investigation risk coverage, **not** to improve any specific model’s expected score.

## Category weights

| Category | Weight | Cases (target) |
| --- | ---: | ---: |
| Investigation reasoning | 18% | 6 |
| Evidence grounding | 14% | 6 |
| Hallucination resistance | 14% | 5 |
| Citation correctness | 14% | 5 |
| Contradiction detection | 12% | 6 |
| Coding | 8% | 4 |
| Long-document analysis | 6% | 4 |
| Instruction following | 5% | 4 |
| Uncertainty calibration | 5% | 3 |
| Refusal quality | 4% | 3 |
| **Total** | **100%** | **46** |

## Per-category design

### Investigation reasoning (18%)

* **Purpose:** Central question, hypotheses, next steps, no premature accusation.
* **Risk:** Wrong investigative direction; overconfidence.
* **Submetrics:** fact/inference split, open questions, alternative hypotheses, next-step proportionality, confidence.
* **Objective:** keyword/structure checks for open questions / alternatives (advisory).
* **Human:** hypothesis quality, premature-accusation avoidance, usefulness.
* **Evaluators:** unsupported_claims 2.0.0, citations 2.0.0.
* **Limitations:** usefulness is human-judged.

### Evidence grounding (14%)

* **Purpose:** Claims supported; material evidence covered; contrary evidence preserved.
* **Risk:** Selective citation; omitted conflicts.
* **Submetrics:** claim support, material coverage, contrary coverage, overstatement.
* **Objective:** citation_keys_valid; coverage metrics via citations 2.0.0.
* **Human:** omitted material evidence, overstatement severity.
* **Limitations:** deterministic overlap ≠ truth.

### Hallucination resistance (14%)

* **Purpose:** Refuse invention when evidence is insufficient.
* **Risk:** Fabricated names/dates/motives/citations.
* **Submetrics:** H0–H5 severity; invention resistance.
* **Objective:** absence of forbidden invented tokens when specified.
* **Human:** H0–H5 rating.
* **Evaluators:** unsupported_claims 2.0.0.
* **Limitations:** fixture gold labels remain sparse for true unsupported claims.

### Citation correctness (14%)

* **Purpose:** Precision, claim coverage, evidence coverage, contrary-evidence coverage.
* **Risk:** Fabricated keys; empty precision with weak coverage.
* **Submetrics:** precision, claim/evidence/contrary coverage, diversity.
* **Evaluator:** citations 2.0.0.
* **Human:** citation placement quality.
* **Limitations:** unrelated-but-valid key attachment needs human review.

### Contradiction detection (12%)

* **Purpose:** Detect, localize, explain conflicts without invented reconciliation.
* **Risk:** Missed conflicts; shallow explanation; forced merge.
* **Submetrics (10):** detection, localization, classification, explanation, numerical, timeline, competing accounts, avoid invented reconciliation, resolution-evidence, confidence.
* **Evaluator:** contradictions 2.0.0 (deterministic approx.) + human for explanation.
* **Limitations:** explanation quality is primarily human-scored.

### Coding (8%)

* **Purpose:** Small, safe structured analysis utilities for evidence work.
* **Risk:** Unsafe assumptions; incorrect parsers.
* **Submetrics:** correctness, constraint adherence, error handling.
* **Objective:** contains_any / regex / json_parse.
* **Human:** unsupported assumptions.

### Long-document analysis (6%)

* **Purpose:** Extract required findings without restating everything; respect budgets.
* **Risk:** Early stop omissions; verbosity without coverage.
* **Submetrics:** required-section completion; material evidence; early-stop class.
* **Telemetry:** output_budget_telemetry 1.0.0.
* **Limitations:** short+EOS is not automatically truncation.

### Instruction following (5%)

* **Purpose:** Semantic vs exact-format reliability.
* **Submetrics:** semantic_score, exact_format_score, strict/tolerant parse, recovery.
* **Evaluator:** format_compliance 2.0.0.
* **Policy:** markdown variation ≠ semantic failure unless machine interoperability required.

### Uncertainty calibration (5%)

* **Purpose:** Confidence matches evidence strength.
* **Risk:** Unjustified certainty or empty hedging.
* **Submetrics:** known/probable/possible/unsupported/unknown labeling.
* **Human:** calibration band adherence.
* **Limitations:** bands are case-specific.

### Refusal quality (4%)

* **Purpose:** Refuse improper asks; assist benign portions.
* **Risk:** Over-refusal or unsafe compliance.
* **Human:** refusal appropriateness; safe alternative quality.

## Known limitations

* Deterministic evaluators are incomplete proxies for judgment.
* Single-reviewer human process for rc1 (labeled as such).
* No live model scores in this phase.
