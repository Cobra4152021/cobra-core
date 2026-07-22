# ADR-0003 — Qwen3-8B Interim CobraBench v0.1 Baseline

- **Status:** Accepted
- **Date:** 2026-07-22
- **Phase:** 2D — Qwen3-8B CobraBench v0.1 interim baseline

## Context

Phase 2C acquired and hash-verified Qwen3-32B but failed local load validation on the RTX 4070 / ~32 GB RAM Windows host. Dual-model baseline evaluation stopped. Phase 2D authorizes an **8B-only** interim baseline to validate the full CobraBench workflow and produce the first category-level scores.

## Why 8B-only evaluation was authorized

- Qwen3-8B is verified, loadable, and interim-eligible on this environment.
- Qwen3-32B is blocked by runtime on this environment (not globally unusable).
- The lab needs an end-to-end scoring/review/reporting dry-run before investing in larger hardware.

## Benchmark version

CobraBench v0.1 (28 cases). Inventory SHA256 `372edd36808909e191a4a6e2b8d012373f3b4a3f1e3831488b866ff6c598bf5a`. Frozen cases were not altered after the run began.

## Evaluation protocol

`evaluations/protocols/qwen3-8b-cobrabench-v0.1.json` — thinking **disabled**, temperature `0`, seed `123`, `max_new_tokens=512`, bitsandbytes 4-bit on official BF16, no silent retries. Run ID `20260722T200000Z-8bba5e01`.

## Results by category

| Category | Score |
| --- | ---: |
| investigation_reasoning | 0.829 |
| evidence_grounding | 0.783 |
| hallucination_resistance | 0.880 |
| citation_correctness | 0.950 |
| contradiction_detection | 0.767 |
| coding | 0.833 |
| long_document_analysis | 0.725 |
| refusal_quality | 0.875 |
| instruction_following | 0.850 |

**Overall interim weighted score: 0.840**

## Citation findings

Mean precision 1.00; mean coverage 0.84; fabricated citations **0**.

## Hallucination findings

Human severity: H0=25, H1=2, H2=1, H3+=0. Automated labels were over-aggressive and are not used as ground truth.

## Contradiction findings

Direct schedule conflicts detected well; numerical mismatch case weaker.

## Refusal findings

Appropriate refusals with safe redirection on credential/destructive prompts.

## Coding findings

Generally correct short solutions for parse/regex/JSON tasks.

## Performance findings

Median latency ~20 s; ~6.2 tok/s under 4-bit hybrid load; 28/28 completed; 0 failures.

## Main strengths

Citation discipline; missing-evidence restraint; refusal quality; investigation structuring.

## Main weaknesses

Long-document completeness under token cap; exact format brittleness; some contradiction depth.

## Decision

Accept Qwen3-8B as an **interim development baseline** for CobraBench workflow validation and weakness observation.

> Qwen3-8B is an interim development baseline. It is not designated Cobra Core, and its results do not establish Qwen3-32B performance.

Do **not** automatically authorize fine-tuning.

### Next authorized options (pick explicitly)

1. Run a Qwen3-8B thinking-mode comparison cohort.  
2. Perform weakness analysis (no training yet).  
3. Test another 8B–14B open model.  
4. Rent/use suitable hardware for Qwen3-32B.  
5. Acquire an approved Qwen3-32B quantized derivative as a separate identity.  
6. Revise CobraBench in v0.1.1/v0.2 based on defect review.  
7. Stop Qwen evaluation.

## Risks

- Over-interpreting interim scores as production readiness.  
- Contaminating future training with benchmark prompts if published early.  
- Treating noisy automated unsupported-claim counts as hallucinations.

## Unknowns

- Native BF16 quality delta vs 4-bit.  
- Thinking-enabled cohort behavior.  
- 32B performance on capable hardware.

## Revisit conditions

Revisit when a second model cohort completes, thinking-mode study completes, or 32B load validation succeeds elsewhere.
