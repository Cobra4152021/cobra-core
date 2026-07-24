# Cobra Core — Product Vision

**Phase:** 4.1 (product definition)  
**Designation status:** Prospective — **Cobra Core** is not yet an officially designated shipping model. This document defines the intended product identity so validation and releases have a fixed north star.

## 1. Primary mission

**Cobra Core** is an evidence-first AI model (and surrounding model lab) optimized for **investigation-grade reasoning**: grounding claims in supplied sources, surfacing contradictions, reporting confidence and unknowns, resisting hallucination, and remaining useful for adjacent research, engineering, and analytical work.

Mission one-liner:

> Help serious analysts answer “what does the evidence support?” — not “what sounds plausible?”

## 2. What Cobra is

| Cobra is | Meaning |
| --- | --- |
| An **evidence-first model family** (target product) | Prioritizes citation discipline, contradiction detection, calibrated confidence |
| A **Model Lab** (this repository) | Intake, benchmarks (CobraBench), evaluation, runtime qualification, future training gates |
| A **runtime-qualified inference stack** (today) | Phase 3F cloud Linux Qwen3-8B path is smoke-qualified for further validation |
| A **workload-validation program** (Phase 4) | Real-user capability suite separate from official CobraBench scores |
| A **future input** to Cobra Investigator | The app consumes models; Core does not become the app |

## 3. What Cobra is not

| Cobra is not | Why |
| --- | --- |
| **Cobra Investigator** | No case UI, Evidence Vault, auth, billing, or production chat endpoints here |
| A general chatbot optimized for vibes / entertainment | Fluency without grounding is a failure mode |
| A replacement for human investigators or counsel | Assistive only; humans own decisions |
| An autonomous agent that publishes, spends, or deletes | No unsupervised external actions |
| “Whatever scores highest on a leaderboard” | Official scores are versioned; gaming prompts for **0.840** is forbidden |
| A guarantee of legal/medical/forensic truth | Outputs are provisional analytical aids |
| Production SaaS by default | Deployment requires separate authorization |

## 4. Intended markets

| Market | Fit | Notes |
| --- | --- | --- |
| Investigative research & OSINT-style analysis | Primary | Source-bound reasoning |
| Public safety / government analytical units | Primary (controlled) | High bar on overclaim & auditability |
| Academic / policy research assistants | Secondary | Long-doc + citation workflows |
| Software teams building evidence products | Secondary | Code + architecture assist around the lab/app |
| Internal business ops / diligence | Tertiary | Planning/docs with grounding habits |
| Consumer open chat | **Non-goal** | Wrong incentives |

## 5. Competitive differentiators

1. **Evidence structure as first-class** — Finding / Evidence / Inference / Confidence / Missing (see evidence prompt standard).  
2. **Contradiction & uncertainty as features** — not bugs to paper over.  
3. **Evaluation integrity** — official scores immutable; RCs labeled; workload validation ≠ benchmark score.  
4. **Runtime qualification discipline** — pinned stacks, smoke gates, cleanup/cost controls before “usefulness” claims.  
5. **Clear product boundary** — model lab vs Investigator application prevents shadow-product sprawl.  
6. **Refusal to overclaim** — naming culprits or inventing sources is an unacceptable failure, not a style issue.

## 6. Product pillars

| Pillar ID | Pillar | Promise |
| --- | --- | --- |
| P1 | Grounding | Claims map to supplied sources or are marked unknown |
| P2 | Contradiction intelligence | Conflicts are explicit, typed, sourced |
| P3 | Calibrated confidence | Strength of belief tracks evidence; unknowns listed |
| P4 | Analytical structure | Timelines, exhibits, structured summaries |
| P5 | Engineering usefulness | Correct, safe code/docs assist without replacing review |
| P6 | Reliability & safety | Stable under repeat; fails safe on malformed/overreach |
| P7 | Operational integrity | Qualified runtime, evidence packages, cost/secret hygiene |

## 7. Long-term roadmap (product, not authorization)

| Horizon | Intent |
| --- | --- |
| Now | Smoke-qualified runtime + docs + Phase 4 framework + product definition (4.1) |
| Near | Authorized Phase 4 execution → Beta gates; optional CobraBench on locked runtime (separate auth) |
| Mid | Iterate model/data only if evidence justifies; keep Investigator integration contract clean |
| Long | Designated Cobra Core release line (versioned); possible larger/specialized variants; training only post-baseline justification |

Training, deployment, and official designation each remain **separately authorized**.

## 8. Integrity invariants

- Official CobraBench v0.1 score remains **0.840** until a new official run.  
- CobraBench v0.2-rc2 remains `prepared-not-run` until authorized.  
- Phase 4 results never replace official scores.  
- No retraining/deployment implied by this vision document.
