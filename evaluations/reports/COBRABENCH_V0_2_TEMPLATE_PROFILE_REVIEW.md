# CobraBench v0.2 Template and Runtime Profile Review

**Phase:** 2H

## Prompt templates (rc1)

| Template | Count | Assessment |
| --- | ---: | --- |
| evidence-analysis@2.0.0 | 38 | Appropriate default for investigation/grounding/citation/hallucination/uncertainty |
| contradiction-analysis@2.0.0 | 6 | Correct for contradiction primary cases |
| exact-format@2.0.0 | 2 | Underused; JSON-only case incorrectly used evidence-analysis |

### rc2 correction

* `cb2-041-json-only`: `evidence-analysis` → `exact-format@2.0.0`

## Runtime profiles

| Profile | Count | Assessment |
| --- | ---: | --- |
| deterministic-investigation | 37 | Adequate max_output_tokens (1024) for most cases |
| structured-json | 5 | Appropriate for coding/JSON instruction cases |
| long-document-analysis | 4 | Required for long-doc category; budgets compatible with concise completion |

## Consistency checks

* Exact-format tasks that require machine parseability now pin exact-format template (rc2).
* Long-document cases already use long-document-analysis profile.
* Templates do not embed gold answers; system prompts are shared (structural repetition, not answer leakage).
* Categories do not receive materially different “coaching” beyond contradiction vs evidence templates.

## Residual limitation

Template concentration remains high (**D2H-010**). Acceptable for rc2; future rc may add category-specific templates without changing weights.
