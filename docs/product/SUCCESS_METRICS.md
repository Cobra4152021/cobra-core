# Success metrics — Cobra Core

Metrics define how we know the product is succeeding. They are **not** a substitute for official CobraBench scores.

**Baseline today:** runtime `phase-3f-qualified`; official score **0.840**; CobraBench `prepared-not-run`; Phase 4 framework complete, **not executed**.

## 1. Metric classes

| Class | Purpose | Examples |
| --- | --- | --- |
| Integrity | Must never regress quietly | Score label, protocol status, pin hashes |
| Runtime | Can we run safely | Smoke Outcome A, cleanup, cost ceiling |
| Workload (Phase 4) | Real-user usefulness | Task pass rate, critical hard-fail count |
| Product gate | Release readiness | Alpha/Beta/RC/1.0 checklists |
| Persona outcome | Value for a user type | Persona pass bars below |

## 2. North-star product metrics (post–Phase 4 execution)

| Metric | Target (Beta+) | Measurement |
| --- | --- | --- |
| Suite task pass rate (Pass or Pass+) | ≥90% of executed catalog tasks | Phase 4 scoring |
| Critical hard fails (U3/U4 grounding/safety) | **0** | Rubric hard-fail override |
| Investigator persona bar | Domain Investigator gate pass + INV-05…08 no hard fail | Domain gates |
| Researcher persona bar | Research domain gate pass + RS-04…06 no hard fail | Domain gates |
| Reliability bar | REL-01 Pass/Pass+; Reliability domain gate pass | Domain gates |
| Repeat stability | REL-01 semantic agreement across 3 runs | Manual/auto compare |
| Official score integrity | Remains **0.840** unless new official run | Audit |
| Protocol integrity | `prepared-not-run` until authorized bench | Audit |

## 3. Persona success criteria

| Persona | Success when… |
| --- | --- |
| Investigator | Can produce sourced timeline + contradiction list + confidence-tagged findings without fabrication on INV/RS critical tasks |
| Researcher | Long-doc and citation tasks Pass/Pass+; structured JSON valid when required |
| Software Engineer | ≥70% Code tasks Pass/Pass+; no credential/destructive hard fails |
| Public Safety / Gov Analyst | Meets Investigator + Reliability bars; INV-08 Pass/Pass+; language remains non-overclaiming |
| Business Analyst | Business domain gate pass; no invented ROI/compliance claims on BZ tasks |

## 4. Product pillars ↔ success signals

| Pillar | Leading indicator tasks | Fail signal |
| --- | --- | --- |
| P1 Grounding | RS-04…06, INV-07 | Ghost citations |
| P2 Contradiction | INV-05…06, RS-06 | Silent merge of conflicts |
| P3 Confidence | INV-07…08 | High confidence / thin evidence |
| P4 Structure | INV-01…04, RS-07…08 | Invented events / invalid schema |
| P5 Engineering | CG-* | Fake APIs / unsafe shell |
| P6 Reliability | REL-* | Flip-flop facts; unsafe parse |
| P7 Ops integrity | Env verify, cleanup, BZ-03/07 | Pin drift; leftover spend |

## 5. Phase 4 task → persona & pillar map

All 46 tasks. Personas: INV=Investigator, RES=Researcher, SWE=Software Engineer, GOV=Public Safety/Gov, BA=Business Analyst.

| Task | Personas | Pillars |
| --- | --- | --- |
| CG-01 | SWE | P5 |
| CG-02 | SWE | P5 |
| CG-03 | SWE | P5 |
| CG-04 | SWE | P5 |
| CG-05 | SWE | P5 |
| CG-06 | SWE, BA | P5 |
| CG-07 | SWE | P5, P7 |
| CG-08 | SWE, GOV | P5, P6 |
| CG-09 | SWE | P5 |
| CG-10 | SWE | P5 |
| CG-11 | SWE | P5 |
| CG-12 | SWE | P5 |
| CG-13 | SWE | P5 |
| CG-14 | SWE | P5 |
| CG-15 | SWE | P5 |
| RS-01 | RES, INV, GOV | P1, P3, P4 |
| RS-02 | RES, GOV | P1, P4 |
| RS-03 | RES, INV, BA | P1, P4 |
| RS-04 | RES, INV, GOV | P1 |
| RS-05 | RES, INV, GOV | P1 |
| RS-06 | RES, INV, GOV | P1, P2 |
| RS-07 | RES, BA | P4 |
| RS-08 | RES, BA, GOV | P4, P3 |
| INV-01 | INV, GOV | P4, P1 |
| INV-02 | INV, GOV | P4, P3 |
| INV-03 | INV, GOV | P4, P1 |
| INV-04 | INV, GOV | P4 |
| INV-05 | INV, GOV | P2 |
| INV-06 | INV, GOV | P2 |
| INV-07 | INV, GOV | P3, P1 |
| INV-08 | INV, GOV | P3, P6 |
| BZ-01 | BA, SWE | P5, P7 |
| BZ-02 | BA | P5 |
| BZ-03 | SWE, BA, GOV | P5, P7 |
| BZ-04 | SWE, BA | P5 |
| BZ-05 | SWE, BA | P5 |
| BZ-06 | SWE, GOV | P5, P6 |
| BZ-07 | SWE, GOV, BA | P7, P6 |
| BZ-08 | SWE, GOV | P7 |
| REL-01 | All | P6 |
| REL-02 | SWE, GOV | P6, P7 |
| REL-03 | RES, INV | P6, P1 |
| REL-04 | All | P6 |
| REL-05 | INV, RES, GOV | P6, P1 |
| REL-06 | RES, INV, GOV | P6, P1 |
| REL-07 | RES, SWE | P6 |

### Coverage counts

| Persona | Tasks mapped (primary or secondary) |
| --- | ---: |
| Investigator | 18 |
| Researcher | 14 |
| Software Engineer | 24 |
| Public Safety / Gov Analyst | 22 |
| Business Analyst | 14 |

| Pillar | Tasks touching pillar |
| --- | ---: |
| P1 Grounding | 16 |
| P2 Contradiction | 4 |
| P3 Confidence | 6 |
| P4 Structure | 12 |
| P5 Engineering | 22 |
| P6 Reliability | 14 |
| P7 Ops integrity | 8 |

*Note:* Tasks may map to multiple personas/pillars; counts are multi-label.

## 6. Non-metrics (explicitly excluded)

- Chatbot arena elo  
- Raw tokens/second as a product success metric (telemetry only)  
- Unversioned “vibes” demos without fixtures  
- Prompt-tuned lifts of official **0.840**
