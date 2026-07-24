# Task catalog — Phase 4 Capability Validation

**Execution status:** Not run (framework only).  
Each task includes: representative prompt intent, success criteria, measurable outputs, failure modes, production usefulness estimate.

Fixtures must be **synthetic / public-safe**. Do not use live case data.

Scoring scale references: `SCORING_RUBRIC.md` (0–3 per dimension).

---

## Domain A — Code generation

### CG-01 — Python: small CLI utility
| Field | Content |
| --- | --- |
| Intent | Implement a Python 3.12 CLI that validates JSON files against required keys and exits non-zero on failure |
| Success criteria | Correct argparse/typer usage; clear errors; no invented deps; handles missing file |
| Measurable outputs | Complete script; example invocation; exit-code table |
| Failure modes | Pseudo-code only; wrong exit codes; unsafe `eval`; hallucinated libraries |
| Usefulness | **High** — daily engineering |

### CG-02 — Python: data transform
| Field | Content |
| --- | --- |
| Intent | Transform a list of dicts: normalize dates ISO-8601, drop null emails, dedupe by id |
| Success criteria | Pure function; edge cases listed; O(n) approach reasonable |
| Measurable outputs | Function + 3 unit-test style examples |
| Failure modes | Silent data loss; timezone invention; mutates input unexpectedly |
| Usefulness | **High** |

### CG-03 — Python: typing / errors
| Field | Content |
| --- | --- |
| Intent | Add type hints and structured error types to a provided stub function |
| Success criteria | Valid typing; no behavior change claimed without proof |
| Measurable outputs | Annotated code; error hierarchy |
| Failure modes | `Any` everywhere; breaks call sites |
| Usefulness | **Med-High** |

### CG-04 — TypeScript: API client
| Field | Content |
| --- | --- |
| Intent | Typed `fetch` wrapper with timeout and JSON error parsing |
| Success criteria | Discriminated result type; no `any` abuse; abort/timeout noted |
| Measurable outputs | `.ts` module + usage snippet |
| Failure modes | Ignores HTTP errors; unbounded retries |
| Usefulness | **High** |

### CG-05 — TypeScript: Zod-like validation sketch
| Field | Content |
| --- | --- |
| Intent | Validate a user profile object with required/optional fields (hand-rolled or zod if stated) |
| Success criteria | Explicit schema; useful error messages |
| Measurable outputs | Validator + failing/passing examples |
| Failure modes | Runtime-unsafe casts; incomplete checks |
| Usefulness | **Med-High** |

### CG-06 — SQL: analytical query
| Field | Content |
| --- | --- |
| Intent | Given schema (users, orders), write SQL for monthly revenue by plan with null-safe totals |
| Success criteria | Correct joins/group by; handles nulls; dialect stated (SQLite/Postgres) |
| Measurable outputs | Single query + brief explain |
| Failure modes | Cartesian join; wrong grain; SQL injection via string concat in app code |
| Usefulness | **High** |

### CG-07 — SQL: migration-safe alter
| Field | Content |
| --- | --- |
| Intent | Add nullable column + index; note online vs lock risks |
| Success criteria | Forward-compatible steps; rollback note |
| Measurable outputs | DDL + checklist |
| Failure modes | Destructive default; missing index caution |
| Usefulness | **Med-High** |

### CG-08 — Shell: safe backup script
| Field | Content |
| --- | --- |
| Intent | Bash script to tar a directory with timestamp; refuse if source missing |
| Success criteria | `set -euo pipefail`; quoting; no `rm -rf` surprises |
| Measurable outputs | Script + dry-run note |
| Failure modes | Unquoted vars; destructive defaults |
| Usefulness | **Med-High** |

### CG-09 — Shell: log grep helper
| Field | Content |
| --- | --- |
| Intent | Find ERROR lines in rotated logs with `grep`/`rg` patterns |
| Success criteria | Correct patterns; performance note for large files |
| Measurable outputs | Commands + example output shape |
| Failure modes | Catastrophic backtracking; wrong flags |
| Usefulness | **Med** |

### CG-10 — Cloudflare Workers: JSON API
| Field | Content |
| --- | --- |
| Intent | Worker `fetch` handler returning JSON health + echo of safe query param |
| Success criteria | Module worker style; no Node-only APIs; CORS note optional |
| Measurable outputs | `src/index.ts` (or JS) + wrangler binding comments |
| Failure modes | Express idioms; assumes filesystem; secrets in code |
| Usefulness | **Med** (stack-specific) |

### CG-11 — Cloudflare Workers: KV/R2 sketch
| Field | Content |
| --- | --- |
| Intent | Read a KV key or R2 object metadata via env bindings (mocked names) |
| Success criteria | Binding usage correct; error if missing |
| Measurable outputs | Handler + env interface |
| Failure modes | Hardcoded credentials; wrong binding names without declare |
| Usefulness | **Med** |

### CG-12 — Debugging: Python traceback
| Field | Content |
| --- | --- |
| Intent | Given a failing snippet + traceback, identify root cause and minimal fix |
| Success criteria | Correct root cause; minimal diff; no unrelated rewrite |
| Measurable outputs | Diagnosis + patched code |
| Failure modes | Wrong line blame; drive-by refactor |
| Usefulness | **High** |

### CG-13 — Debugging: async race sketch
| Field | Content |
| --- | --- |
| Intent | Explain a provided racey async pattern and fix with ordering/lock/queue |
| Success criteria | Plausible race explanation; safe fix |
| Measurable outputs | Before/after + why |
| Failure modes | Ignores concurrency; adds sleep-only “fix” |
| Usefulness | **Med-High** |

### CG-14 — Refactor: extract pure helpers
| Field | Content |
| --- | --- |
| Intent | Refactor a messy function into testable helpers without behavior change |
| Success criteria | Clear structure; lists preserved behaviors |
| Measurable outputs | Refactored code + behavior checklist |
| Failure modes | Silent semantics change; over-abstraction |
| Usefulness | **Med-High** |

### CG-15 — Refactor: naming / dead code
| Field | Content |
| --- | --- |
| Intent | Improve names and remove clearly dead branches in a short module |
| Success criteria | Safer readability; no speculative deletion of maybe-live paths without note |
| Measurable outputs | Diff-style output + risks |
| Failure modes | Deletes ambiguous code; renames inconsistently |
| Usefulness | **Med** |

---

## Domain B — Research

### RS-01 — Long-form multi-source brief
| Field | Content |
| --- | --- |
| Intent | 800–1500 word brief from 3 synthetic sources; separate fact vs inference |
| Success criteria | Covers all sources; no invented citations; confidence called out |
| Measurable outputs | Brief with Finding/Evidence/Inference sections |
| Failure modes | Hallucinated sources; merges conflicting claims |
| Usefulness | **High** |

### RS-02 — Section-faithful synthesis
| Field | Content |
| --- | --- |
| Intent | Answer 5 questions strictly from a long synthetic document (~3–6k tokens) |
| Success criteria | Each answer grounded; “unknown” when absent |
| Measurable outputs | Q→A list with source anchors |
| Failure modes | Answer from prior knowledge; skipped questions |
| Usefulness | **High** |

### RS-03 — Evidence extraction table
| Field | Content |
| --- | --- |
| Intent | Extract entities, dates, amounts into a table from mixed prose |
| Success criteria | Cell-level accuracy; blanks for missing |
| Measurable outputs | Markdown/CSV table |
| Failure modes | Fabricated amounts; wrong dates |
| Usefulness | **High** |

### RS-04 — Quote fidelity
| Field | Content |
| --- | --- |
| Intent | Provide 3 supporting quotes with exact spans for a claim that is only partly supported |
| Success criteria | Quotes verbatim; notes partial support |
| Measurable outputs | Quote list + support level |
| Failure modes | Paraphrase presented as quote; overclaim |
| Usefulness | **Critical** for trust |

### RS-05 — Citation consistency
| Field | Content |
| --- | --- |
| Intent | Write findings using only `[S1]`/`[S2]` IDs supplied; refuse extra IDs |
| Success criteria | Every claim tagged; no `[S9]` invention |
| Measurable outputs | Tagged findings list |
| Failure modes | Ghost citations; untagged claims |
| Usefulness | **Critical** |

### RS-06 — Conflicting citation resolution
| Field | Content |
| --- | --- |
| Intent | Two sources disagree on a date; report conflict, not a false average |
| Success criteria | Explicit contradiction; no forced pick without rationale |
| Measurable outputs | Conflict record + confidence |
| Failure modes | Picks one silently; invents reconciler source |
| Usefulness | **Critical** |

### RS-07 — Structured summary JSON
| Field | Content |
| --- | --- |
| Intent | Emit JSON: `{title, key_points[], risks[], open_questions[]}` from a memo |
| Success criteria | Valid JSON; schema complete; points grounded |
| Measurable outputs | Parseable JSON only (or fenced) |
| Failure modes | Invalid JSON; empty required arrays without cause |
| Usefulness | **High** |

### RS-08 — Executive vs technical summary pair
| Field | Content |
| --- | --- |
| Intent | Same source → 5-bullet exec + technical appendix |
| Success criteria | No contradiction between layers; tech has more precision |
| Measurable outputs | Two clearly labeled blocks |
| Failure modes | Exec invents ROI numbers |
| Usefulness | **Med-High** |

---

## Domain C — Investigator

### INV-01 — Timeline from mixed events
| Field | Content |
| --- | --- |
| Intent | Build chronological timeline from unordered event snippets with source IDs |
| Success criteria | Sorted; each event sourced; uncertain dates marked |
| Measurable outputs | Timeline table (time, event, source, confidence) |
| Failure modes | Wrong order; invented events |
| Usefulness | **High** |

### INV-02 — Timeline with gaps
| Field | Content |
| --- | --- |
| Intent | Same as INV-01 but sources omit a middle period; must surface gap |
| Success criteria | Explicit gap callout; no filled fiction |
| Measurable outputs | Timeline + `gaps[]` |
| Failure modes | Smooths over missing time |
| Usefulness | **High** |

### INV-03 — Evidence organization
| Field | Content |
| --- | --- |
| Intent | Cluster 8 snippets into themes (motive, opportunity, reliability) without new facts |
| Success criteria | Every snippet placed or “unclassified”; no theme without support |
| Measurable outputs | Theme → snippet IDs map |
| Failure modes | Narrative embroidery |
| Usefulness | **High** |

### INV-04 — Exhibit list
| Field | Content |
| --- | --- |
| Intent | Produce exhibit register: ID, description, source, sensitivity |
| Success criteria | Stable IDs; no duplicate exhibits for same snippet without note |
| Measurable outputs | Exhibit table |
| Failure modes | Missing sensitivity; merged distinct items |
| Usefulness | **Med-High** |

### INV-05 — Contradiction detection
| Field | Content |
| --- | --- |
| Intent | Find all contradictions among 4 short witness statements |
| Success criteria | Lists each pair + fields that conflict |
| Measurable outputs | Contradiction array |
| Failure modes | Misses direct conflict; invents conflict |
| Usefulness | **Critical** |

### INV-06 — Soft vs hard contradiction
| Field | Content |
| --- | --- |
| Intent | Label conflicts as hard (mutually exclusive) vs soft (tension) |
| Success criteria | Correct labels on seeded examples |
| Measurable outputs | Labeled list + rationale |
| Failure modes | Treats all tension as fraud |
| Usefulness | **High** |

### INV-07 — Confidence reporting
| Field | Content |
| --- | --- |
| Intent | Answer 3 investigative questions with Finding/Evidence/Confidence/Missing |
| Success criteria | Confidence tracks evidence strength; missing info non-empty when warranted |
| Measurable outputs | Structured answers |
| Failure modes | High confidence on thin evidence |
| Usefulness | **Critical** |

### INV-08 — Overclaim refusal
| Field | Content |
| --- | --- |
| Intent | User asks for a definitive culprit; evidence insufficient — model must refuse overclaim |
| Success criteria | States insufficiency; offers next collection steps |
| Measurable outputs | Refusal + rationale + next steps |
| Failure modes | Names perpetrator anyway |
| Usefulness | **Critical** |

---

## Domain D — Business

### BZ-01 — Delivery plan
| Field | Content |
| --- | --- |
| Intent | 4-week plan to ship an internal evaluation dashboard (phases, risks, owners roles) |
| Success criteria | Phased; dependencies; risks realistic |
| Measurable outputs | Plan table + risk register |
| Failure modes | Fantasy staffing; no risks |
| Usefulness | **Med-High** |

### BZ-02 — Cost/time tradeoff memo
| Field | Content |
| --- | --- |
| Intent | Compare build vs buy for a small RAG helper using provided constraints |
| Success criteria | Decision criteria explicit; recommendation tied to constraints |
| Measurable outputs | Memo ≤1 page |
| Failure modes | Ignores constraints; vendor hallucination |
| Usefulness | **Med** |

### BZ-03 — Technical documentation
| Field | Content |
| --- | --- |
| Intent | Document the qualified cloud runtime bring-up for a new engineer (from public repo docs only) |
| Success criteria | Accurate vs `docs/operations`; no secret values |
| Measurable outputs | Runbook sections |
| Failure modes | Invents flags; embeds keys |
| Usefulness | **High** |

### BZ-04 — API docstring pack
| Field | Content |
| --- | --- |
| Intent | Write user-facing docs for 3 synthetic REST endpoints |
| Success criteria | Request/response examples; error codes |
| Measurable outputs | Markdown reference |
| Failure modes | Undocumented errors; inconsistent field names |
| Usefulness | **Med-High** |

### BZ-05 — Architecture review
| Field | Content |
| --- | --- |
| Intent | Review a proposed single-Worker + D1 + R2 design; list risks and alternatives |
| Success criteria | ≥5 concrete risks; ≥2 alternatives; no fake CVE claims |
| Measurable outputs | Review note |
| Failure modes | Generic fluff; confidence theater |
| Usefulness | **Med-High** |

### BZ-06 — Threat-informed review
| Field | Content |
| --- | --- |
| Intent | Threat model sketch (STRIDE-lite) for uploading evaluation artifacts |
| Success criteria | Assets, threats, mitigations mapped |
| Measurable outputs | Table |
| Failure modes | Misses obvious IDOR/secret paths |
| Usefulness | **Med-High** |

### BZ-07 — SOP: incident cleanup
| Field | Content |
| --- | --- |
| Intent | SOP to terminate runaway GPU pod and verify zero spend |
| Success criteria | Steps, checks, escalation, rollback/notes |
| Measurable outputs | SOP with checklist |
| Failure modes | Skips verification; destructive ambiguity |
| Usefulness | **Med** |

### BZ-08 — SOP: model intake verify
| Field | Content |
| --- | --- |
| Intent | SOP for verifying inventory hash before qualification |
| Success criteria | Commands + pass/fail; no weight-in-git advice |
| Measurable outputs | SOP |
| Failure modes | Wrong hash procedure |
| Usefulness | **Med** |

---

## Domain E — Reliability

### REL-01 — Repeated identical prompts
| Field | Content |
| --- | --- |
| Intent | Run same grounded Q&A prompt N=3 (fresh process); compare semantic equivalence |
| Success criteria | Same findings/citations; formatting may differ |
| Measurable outputs | 3 outputs + equivalence score |
| Failure modes | Flip-flop on facts; dropped citations |
| Usefulness | **Critical** |

### REL-02 — Temperature / seed note
| Field | Content |
| --- | --- |
| Intent | Document observed variance under fixed seed if supported; else record “unsupported” |
| Success criteria | Honest capability report; no fake determinism claims |
| Measurable outputs | Telemetry note |
| Failure modes | Claims bit-identical when not |
| Usefulness | **High** (ops trust) |

### REL-03 — Short vs long answer stability
| Field | Content |
| --- | --- |
| Intent | Same facts requested as bullets vs prose; facts must not conflict |
| Success criteria | No cross-format contradiction |
| Measurable outputs | Pair + diff of claims |
| Failure modes | Prose invents extra “facts” |
| Usefulness | **High** |

### REL-04 — Malformed JSON input
| Field | Content |
| --- | --- |
| Intent | User provides broken JSON schema request; model should clarify or safely reject |
| Success criteria | No pretend-parse success; actionable repair hint |
| Measurable outputs | Response |
| Failure modes | Invents parsed fields |
| Usefulness | **High** |

### REL-05 — Contradictory instructions
| Field | Content |
| --- | --- |
| Intent | “Only use S1” and “Prefer S2 when conflict” simultaneously |
| Success criteria | Surfaces instruction conflict; asks or states precedence |
| Measurable outputs | Meta-response |
| Failure modes | Silently picks without note |
| Usefulness | **Med-High** |

### REL-06 — Large context needle
| Field | Content |
| --- | --- |
| Intent | Hide a unique fact mid ~6–12k token synthetic doc; ask for that fact |
| Success criteria | Recovers fact or honestly fails |
| Measurable outputs | Answer + location cue |
| Failure modes | Confident wrong needle |
| Usefulness | **High** |

### REL-07 — Large context aggregation
| Field | Content |
| --- | --- |
| Intent | Count occurrences of a marker token across a long doc |
| Success criteria | Correct count ±0 on seeded doc; show method |
| Measurable outputs | Number + brief method |
| Failure modes | Approximate guess presented as exact |
| Usefulness | **Med-High** |

---

## Task count summary

| Domain | Task IDs | Count |
| --- | --- | --- |
| Code | CG-01…15 | 15 |
| Research | RS-01…08 | 8 |
| Investigator | INV-01…08 | 8 |
| Business | BZ-01…08 | 8 |
| Reliability | REL-01…07 | 7 |
| **Total** | | **46** |
