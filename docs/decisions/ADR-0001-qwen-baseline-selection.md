# ADR-0001 — Qwen Baseline Selection

- **Status:** Accepted (intake / acquisition authorization only)
- **Date:** 2026-07-22
- **Phase:** 2A — Qwen Model Intake and Candidate Selection

## Context

Cobra Model Lab needs a first open-weight Qwen checkpoint for CobraBench baseline evaluation. Phase 1 delivered schemas, synthetic cases, and provider placeholders. Phase 2A must choose candidates from authoritative sources without downloading weights, running inference, or fine-tuning.

Cobra Core targets evidence-first investigation behavior: grounding, citation discipline, contradiction detection, long-document analysis, coding, and hallucination resistance. The initial checkpoint must be practical to self-host, license-clear for research and potential commercial derivative work, and suitable for later LoRA experimentation.

## Decision

1. **Primary baseline:** `Qwen/Qwen3-32B` @ Hub commit `9216db5781bf21249d130ec9da846c4624c16137`  
2. **Resource-constrained / development baseline:** `Qwen/Qwen3-8B` @ Hub commit `b968826d9c46dd6066d109eabc6255188de91218`  
3. **Reasoning challenger (acquire after primary):** `Qwen/Qwen3-30B-A3B-Thinking-2507` @ Hub commit `144afc2f379b542fdd4e85a1fcd5e1f79112d95d`  
4. **No separate coding challenger** for Phase 2A initial intake.

> **This selection authorizes acquisition and baseline evaluation only. It does not designate the model as Cobra Core.**

## Candidate models considered

| Model | Outcome |
| --- | --- |
| Qwen3-32B | Selected primary |
| Qwen3-8B | Selected development baseline |
| Qwen3-30B-A3B-Thinking-2507 | Selected reasoning challenger (deferred acquisition) |
| Qwen3-4B | Rejected as named role (overlaps 8B) |
| Qwen3-14B | Rejected (middle ground without role clarity) |
| Qwen3-30B-A3B-Instruct-2507 | Deferred to comparative phase |
| Qwen3-235B-A22B family | Rejected for Phase 2A practicality |
| Qwen2.5-Coder-32B-Instruct | Deferred; not required initially |
| Qwen2.5-72B-Instruct | Rejected (license tag `other` + size) |

Details and score tables: `docs/QWEN_CANDIDATE_ANALYSIS.md`.

## Selection criteria

Intake estimates (not CobraBench results), weighted:

- Investigation potential 20%  
- Evidence-grounding potential 15%  
- Hallucination-resistance potential 15%  
- Citation and attribution potential 10%  
- Long-context capability 10%  
- Coding capability 10%  
- Local deployment practicality 10%  
- Fine-tuning practicality 5%  
- License and commercial suitability 5%  

Category scores retained in the analysis document.

## Selected primary baseline

**Qwen3-32B** — dense hybrid thinking/non-thinking model, Apache-2.0, native 32K context (YaRN 128K), official multi-framework support, strongest practical single checkpoint for full CobraBench.

## Selected smaller development model

**Qwen3-8B** — same hybrid family; official BF16 Transformers short-context footprint ~16 GB GPU memory per Qwen speed benchmark; justified for CI smoke tests and repeated regression loops.

## Alternatives rejected

- **MoE-first primary (30B-A3B / 235B-A22B):** higher serving complexity before a dense baseline exists.  
- **Qwen2.5-72B:** weaker license clarity on Hub (`license: other`) and heavier dense footprint.  
- **Forced coding specialist:** premature before measuring Qwen3-32B coding category results.

## Risks

- Thinking mode may increase verbosity and citation noise.  
- ~63 GB-class BF16 memory need may force AWQ before full baseline completeness.  
- Intake scores for grounding/hallucination are speculative until CobraBench runs.  
- Hub commit pins can be superseded by newer Qwen3 releases.

## Unknowns

- Real CobraBench category performance  
- Whether 256K MoE challenger is necessary after 32K/YaRN dense baseline  
- Exact on-disk shard byte totals (Hub API sizes unavailable during intake)  
- Optimal sampling settings for investigation tasks vs official math/coding guidance

## Revisit conditions

Reopen this ADR if:

1. Authorized hardware cannot run Qwen3-32B BF16 or quality-preserving AWQ.  
2. A newer Apache-2.0 Qwen dense model clearly dominates 32B on official reports.  
3. Baseline shows coding-category failure justifying Qwen2.5-Coder comparative intake.  
4. Long-document cases require native ≥256K context.

## Next step

Execute `docs/QWEN_ACQUISITION_PLAN.md` **only after separate authorization**. Then run Phase 2 baseline evaluation — still without designating any checkpoint as Cobra Core.
