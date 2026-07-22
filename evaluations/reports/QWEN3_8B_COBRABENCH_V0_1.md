# Qwen3-8B — CobraBench v0.1 Interim Baseline Report

**Status:** Interim baseline complete (single-model).  
**Label:** Qwen3-8B CobraBench v0.1 interim baseline score  
**Overall interim weighted score:** **0.840**  
**Not Cobra Core.** Results do not establish Qwen3-32B performance.

## Executive summary

Qwen3-8B completed all **28/28** CobraBench v0.1 cases under a frozen protocol (thinking disabled, temperature 0, seed 123, max_new_tokens 512, bitsandbytes 4-bit on official BF16). Human review covered **100%** of cases. LLM-as-judge was **not run** (no pinned external judge). Strongest areas: citation discipline, instruction following, investigation/refusal. Weakest: long-document completeness under the token cap and one numerical-contradiction case.

## Model / benchmark / runtime

| Field | Value |
| --- | --- |
| Model | `Qwen/Qwen3-8B` |
| Revision | `b968826d9c46dd6066d109eabc6255188de91218` |
| Benchmark | CobraBench v0.1 (28 cases) |
| Inventory SHA256 | `372edd36808909e191a4a6e2b8d012373f3b4a3f1e3831488b866ff6c598bf5a` |
| Protocol | `evaluations/protocols/qwen3-8b-cobrabench-v0.1.json` |
| Thinking | **disabled** |
| Temperature / seed | `0.0` / `123` |
| max_new_tokens | `512` |
| Precision | bitsandbytes 4-bit NF4 from official BF16 |
| device_map / max_memory | `auto` / `{0:"9GiB","cpu":"18GiB"}` |
| Environment | `local-windows-rtx4070-12gb` |
| Run ID | `20260722T200000Z-8bba5e01` |

## Category-level scores (human primary)

| Category | Weight | Score |
| --- | ---: | ---: |
| investigation_reasoning | 0.20 | 0.829 |
| evidence_grounding | 0.15 | 0.783 |
| hallucination_resistance | 0.15 | 0.880 |
| citation_correctness | 0.15 | 0.950 |
| contradiction_detection | 0.10 | 0.767 |
| coding | 0.10 | 0.833 |
| long_document_analysis | 0.05 | 0.725 |
| refusal_quality | 0.05 | 0.875 |
| instruction_following | 0.05 | 0.850 |

**Qwen3-8B CobraBench v0.1 interim baseline score (weighted): 0.840**

## Objective metrics

| Metric | Value |
| --- | --- |
| Successful runs | 28 |
| Failed runs | 0 |
| Retries | 0 |
| Input tokens (total) | 4473 |
| Output tokens (total) | 5286 |
| Median latency | ~20.1 s |
| Mean latency | ~30.6 s |
| P90 latency | ~79.6 s |
| Median tok/s | ~6.22 |
| Mean tok/s | ~6.22 |

## Rule-based checks

Per-case objective and behavior checks are preserved in the run’s `rule-checks.json`. Failed rules retain rule ID, expected condition, observed result, and score effect. Keyword behavior heuristics are assistive only.

## Human review

| Item | Value |
| --- | --- |
| Coverage | 28/28 (100%) |
| Required categories reviewed | citation, hallucination, contradiction, refusal (all) |
| Rationales | Present for every scored case |
| Separation | Human scores stored separately from objective/rule/judge |

## Judge results

**Not run.** No pinned external judge model was configured for this phase.

## Citation metrics

| Metric | Value |
| --- | --- |
| Precision (mean) | 1.00 |
| Coverage (mean) | 0.84 |
| Fabricated citation count | **0** |
| Unsupported-claim count (automated heuristic) | 172 — **not definitive**; see defect review |

## Hallucination severity (human layer)

| Severity | Cases |
| --- | ---: |
| H0 | 25 |
| H1 | 2 |
| H2 | 1 |
| H3–H5 | 0 |

Automated severity labels over-fired (many H3); human review is authoritative for this interim baseline.

## Contradiction / refusal / coding / long-doc / instruction

- **Contradiction:** Schedule conflict case strong; metric conflict weaker (0.55 on `cb-019`).  
- **Refusal:** Credential and destructive-action cases established boundaries with safe redirection.  
- **Coding:** Short Python/regex/JSON tasks generally correct.  
- **Long-document:** Partial under 512-token cap; content mostly grounded.  
- **Instruction-following:** JSON-only strong; exact FINDING/RISK/NEXT format partially missed via markdown bullets.

## Strongest recurring behaviors

- Citation key discipline without fabricating SRC-* IDs.  
- Explicit insufficient-information posture on missing evidence.  
- Clear refusal + safe alternative for credential requests.

## Weakest recurring behaviors

- Long-document completeness vs token budget.  
- Occasional format brittleness on exact instruction templates.  
- Numerical contradiction explanation depth.

## Runtime failures

None. All cases status `ok`.

## Limitations

- Interim single-model baseline only.  
- 4-bit load ≠ native BF16.  
- Heuristic auto unsupported-claim / hallucination layers are noisy.  
- Human review is structured single-reviewer interim judgment, not multi-rater adjudication.  
- Small synthetic suite (28 cases).

## Recommended next phase (authorization required)

Weakness analysis, thinking-mode cohort, alternate mid-size open model, or suitable hardware for Qwen3-32B — **not** automatic fine-tuning.
