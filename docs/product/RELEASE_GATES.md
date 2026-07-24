# Release gates — Cobra Core

Gates apply to **future product/runtime releases** of the Cobra Core line. Passing a gate requires evidence, not aspiration.

**Current assessed stage:** **Alpha (documentation + runtime qualification complete; capability execution pending).**  
See §6 for readiness snapshot.

## Gate conventions

| Term | Meaning |
| --- | --- |
| Critical failure | Rubric hard fail on grounding (U3) or safety/overclaim (U4); or secret leakage; or pin drift during a claimed validation run |
| Capability validation | Phase 4 suite per `docs/capability-validation/` |
| Operational readiness | Ops + DR + security docs reviewed; cleanup proven for any cloud run used |

---

## Alpha

**Intent:** Safe to continue internal validation; not for external “product” claims.

| Requirement | Evidence | Status (as of Phase 4.1) |
| --- | --- | --- |
| Runtime qualified | `phase-3f-qualified` / Outcome A freeze | **Met** |
| Documentation complete (lab + ops + 3G.5 package) | `docs/operations/`, `docs/architecture/`, readiness report | **Met** |
| Capability framework complete | `docs/capability-validation/` | **Met** |
| Product definition complete | `docs/product/` (this package) | **Met** (this phase) |
| No deployment / no training implied | Governance | **Met** |
| Official score integrity | **0.840**; bench `prepared-not-run` | **Met** |

**Alpha exit:** All rows Met → Alpha declared. *(Achieved with Phase 4.1 docs.)*

---

## Beta

**Intent:** Workload usefulness demonstrated under locked runtime.

| Requirement | Evidence | Status |
| --- | --- | --- |
| Capability validation **executed** on qualified runtime | Phase 4 `SUITE_SUMMARY` + task scores | **Not met** (not executed) |
| ≥90% task pass rate (Pass or Pass+) | Suite aggregate | **Not met** |
| No critical failures | Zero U3/U4 hard fails; no secrets in outputs | **Not met** |
| Persona bars for Investigator + Researcher | Per `SUCCESS_METRICS.md` | **Not met** |
| Reliability domain gate passed | Incl. REL-01 | **Not met** |
| Pins unchanged vs qualified runtime (or new requal) | `phase3g_verify_env` / freeze | Pending execution |

**Beta entry rule:** Separate authorization to spend/run Phase 4 required.

---

## Release Candidate (RC)

**Intent:** Stable, reproducible, operable by another engineer.

| Requirement | Evidence | Status |
| --- | --- | --- |
| Repeated validation stable | Second full or agreed spot-check wave; REL-01 still Pass+ | **Not met** |
| Reproducible evidence package | Hashes, env snapshot, fixtures, SHA256SUMS | **Not met** |
| Operational documentation complete | Ops + DR + checklist exercised | Partially met (docs exist; drill not done) |
| No Suite Invalid conditions | No bench gaming; no mid-run prompt tuning | Pending |
| Security review current | `docs/security/SECURITY_REVIEW.md` + delta notes | Docs met; re-affirm at RC |
| Product positioning / vision unchanged or versioned | `docs/product/` | Met as baseline |

---

## Version 1.0

**Intent:** First designated Cobra Core product release line (still not Investigator).

| Requirement | Evidence | Status |
| --- | --- | --- |
| Capability validated (Beta + RC satisfied) | Frozen validation release dir | **Not met** |
| Production documentation complete | Vision, personas, metrics, gates, ops, DR, GPU matrix | Docs largely present; “production” approval pending |
| Operational readiness approved | Explicit sign-off record (future ADR or release note) | **Not met** |
| Designation decision recorded | ADR: “designate Cobra Core v1.0” | **Not met** |
| Deployment policy explicit | Deploy forbidden **or** separately authorized deploy runbook | Default: not deployed |
| Training policy explicit | Training still gated unless authorized | Default: no training |

**1.0 does not require** public SaaS, marketplace listing, or Investigator feature-complete.

---

## Mapping suggested gates → evidence systems

| Gate | Primary evidence home |
| --- | --- |
| Alpha | `docs/releases/phase-3f/`, `docs/capability-validation/`, `docs/product/`, `docs/PRODUCTION_READINESS_REPORT.md` |
| Beta | `evaluations/diagnostics/phase-4-capability-validation/` (future) |
| RC | Re-run package + `docs/operations/` drill record |
| 1.0 | `docs/releases/cobra-core-v1.0/` (future) + designation ADR |

## Relationship to CobraBench

| Gate | CobraBench required? |
| --- | --- |
| Alpha | No |
| Beta | No (workload suite only) |
| RC | Optional; if run, must be separately authorized and labeled |
| 1.0 | Recommended but **not** defined as mandatory in this document; if absent, release notes must say so |

Official **0.840** is never replaced by Phase 4 pass rate.
