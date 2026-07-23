# Milestone M1 — Benchmark Engineering Freeze

**Status:** Frozen documentation milestone  
**Date:** 2026-07-23  
**Phase:** 3A

This milestone freezes completed CobraBench engineering through Phase 2I.  
It does **not** release final CobraBench v0.2 and does **not** designate Cobra Core.

## Official versus release-candidate status

| Artifact | Status | Supersedes official? |
| --- | --- | --- |
| **CobraBench v0.1** | **Official** | — |
| CobraBench v0.2-rc1 | Release candidate (immutable) | **No** |
| CobraBench v0.2-rc2 | Release candidate (immutable, non-final) | **No** |
| CobraBench v0.2 final | Not released | — |

Neither rc1 nor rc2 supersedes the official CobraBench v0.1 benchmark or the official Qwen3-8B score of **0.840**.

## Frozen hashes

### Official Phase 2D baseline (CobraBench v0.1)

* Official Qwen3-8B weighted score: **0.840**
* Result inventory hash:  
  `84b0972fc0c028e5e38392d64e438d7eca473c6d2157ade085534cfead9a1de6`
* Lock: `evaluations/baselines/qwen3-8b-cobrabench-v0.1.json`

### CobraBench v0.2-rc1

* Inventory hash:  
  `87ed4156a3b75cc5c177d29e9bed4e8ebe1b95146c4d9ced14f60fbec75ada87`
* Tree hash:  
  `3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10`

### CobraBench v0.2-rc2

* Inventory hash:  
  `08f04c10267b3f772d7783a332d816947486812f7a983dff070bdad442708cc6`
* Tree hash:  
  `1d438415c22827155f57817ace9274aee6c9e47048e4f6443a249ba7a5f2314f`

## Phase summary (2D–2I)

### Phase 2D — Official interim baseline

| Field | Value |
| --- | --- |
| Commit | `bae09a5` (`feat: add Qwen3-8B CobraBench interim baseline`) |
| Purpose | Establish official Qwen3-8B CobraBench v0.1 interim baseline |
| Outcome | Official weighted score **0.840**; baseline lock frozen |
| Benchmark status | Official v0.1 |
| ADR | ADR-0003 |
| Known limitations | Interim baseline; evaluator v1 limitations later audited |

### Phase 2E — Static weakness analysis

| Field | Value |
| --- | --- |
| Commit | `304ba65` (`feat: add Qwen3-8B weakness analysis and diagnostic framework`) |
| Purpose | Static taxonomy of weaknesses; diagnostic framework |
| Outcome | Live diagnostics deferred; unsupported-claim v1 noise identified |
| Tests (era) | Quality suite green at phase close |
| Benchmark status | v0.1 unchanged |
| ADR | ADR-0004 |
| Known limitations | Live GPU diagnostics blocked; deferred |

### Phase 2F — Evaluators, parsers, prompts, telemetry

| Field | Value |
| --- | --- |
| Commit | `41d5fd6` (`feat: improve Cobra evaluation prompts parsers and scoring`) |
| Purpose | Versioned evaluators/parsers/prompts/runtime profiles; draft v0.2 schema |
| Outcome | Unsupported-claim v2; semantic vs exact format; citation/contradiction upgrades |
| Tests (era) | 135 passed, 1 deselected |
| Benchmark status | Official v0.1 and 0.840 unchanged |
| ADR | ADR-0005 |
| Known limitations | Framework only; historical scores not recalculated |

### Phase 2G — CobraBench v0.2-rc1

| Field | Value |
| --- | --- |
| Commit | `5d57cea` (`feat: add CobraBench v0.2 release candidate`) |
| Purpose | Construct safe 46-case v0.2 release candidate |
| Outcome | rc1 frozen; protocol prepared-not-run; no model eval |
| Tests (era) | 152 passed, 1 deselected |
| Benchmark status | rc1 non-final; v0.1 official |
| ADR | ADR-0006 |
| Known limitations | Single-reviewer authoring/approval; not final |

### Phase 2H — Independent review → rc2

| Field | Value |
| --- | --- |
| Commit | `ade3063` (`feat: add independently reviewed CobraBench v0.2 rc2`) |
| Purpose | Independent static review of rc1; correct material defects |
| Outcome | Outcome B — create rc2; D3 defects addressed; final not released |
| Tests (era) | 165 passed, 1 deselected |
| Benchmark status | rc1 immutable; rc2 non-final |
| ADR | ADR-0007 |
| Known limitations | Single-reviewer; same-org workflow; UC/contradiction proxy limits |

### Phase 2I — Second review → Outcome D

| Field | Value |
| --- | --- |
| Commit | `4278493` (`docs: add second review of CobraBench v0.2 rc2`) |
| Purpose | Second review of rc2; finalization decision |
| Outcome | **Outcome D** — keep rc2 non-final (genuine second-reviewer separation not achieved) |
| Tests (era) | 177 passed, 1 deselected |
| Benchmark status | Official v0.1; rc1/rc2 immutable non-final RCs |
| ADR | ADR-0008 |
| Known limitations | No separate human second reviewer; UC v2 FN risk; small-n refusal/uncertainty |

## ADR index (M1)

* ADR-0003 — Qwen3-8B interim baseline
* ADR-0004 — Weakness analysis / diagnostics posture
* ADR-0005 — Evaluator/framework improvements
* ADR-0006 — CobraBench v0.2-rc1
* ADR-0007 — Independent review and rc2
* ADR-0008 — Second review Outcome D
* ADR-0009 — Review governance (Phase 3A)

## Explicit non-claims

* No model is designated **Cobra Core**.
* No model was evaluated on rc1 or rc2 during M1 freeze documentation.
* No training or fine-tuning was authorized or performed as part of M1.
* Final CobraBench v0.2 is **not** released.
