# Capability matrix (framework)

Usefulness estimates are **prior hypotheses** for planning — not measured results. Update only after authorized execution.

| ID | Domain | Capability | Tasks (catalog) | Success focus | Est. usefulness (hypothesis) | Priority |
| --- | --- | --- | --- | --- | --- | --- |
| CG-PY | Code | Python generation | CG-01…03 | Correct, runnable, typed where asked | High | P0 |
| CG-TS | Code | TypeScript generation | CG-04…05 | Types compile-intent, clear APIs | High | P0 |
| CG-SQL | Code | SQL | CG-06…07 | Correct joins/filters; safe patterns | High | P0 |
| CG-SH | Code | Shell | CG-08…09 | Idempotent-safe scripts; quoting | Med-High | P1 |
| CG-CF | Code | Cloudflare Workers | CG-10…11 | Fetch handlers, bindings-aware | Med | P1 |
| CG-DBG | Code | Debugging | CG-12…13 | Root cause + minimal fix | High | P0 |
| CG-REF | Code | Refactoring | CG-14…15 | Behavior-preserving structure | Med-High | P1 |
| RS-LD | Research | Long-form reasoning | RS-01…02 | Faithful multi-section synthesis | High | P0 |
| RS-EX | Research | Evidence extraction | RS-03…04 | Span-accurate claims | High | P0 |
| RS-CIT | Research | Citation consistency | RS-05…06 | No invented sources; ID match | Critical | P0 |
| RS-SUM | Research | Structured summaries | RS-07…08 | Schema adherence | High | P0 |
| INV-TL | Investigator | Timeline construction | INV-01…02 | Ordered, sourced events | High | P0 |
| INV-EO | Investigator | Evidence organization | INV-03…04 | Grouping without invention | High | P0 |
| INV-CD | Investigator | Contradiction detection | INV-05…06 | Explicit conflicts + sources | Critical | P0 |
| INV-CF | Investigator | Confidence reporting | INV-07…08 | Calibrated; lists unknowns | High | P0 |
| BZ-PL | Business | Planning | BZ-01…02 | Actionable phased plan | Med-High | P1 |
| BZ-DOC | Business | Technical documentation | BZ-03…04 | Accurate, scannable | High | P1 |
| BZ-AR | Business | Architecture review | BZ-05…06 | Risks + alternatives | Med-High | P1 |
| BZ-SOP | Business | SOP generation | BZ-07…08 | Steps, checks, rollback | Med | P2 |
| REL-RP | Reliability | Repeated prompts | REL-01 | Semantic stability | Critical | P0 |
| REL-DET | Reliability | Determinism controls | REL-02…03 | Seed/temp behavior documented | High | P0 |
| REL-MAL | Reliability | Malformed inputs | REL-04…05 | Safe refusal / clarify | High | P0 |
| REL-CTX | Reliability | Large context | REL-06…07 | No silent drop of key facts | High | P0 |

**Legend — Est. usefulness:** planning prior for Investigator/research-heavy mission; revise after scoring.
