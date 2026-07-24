# Production Readiness Report — Phase 3G.5

**Mission:** Documentation and engineering review only.  
**Baseline runtime:** `phase-3f-qualified` / `0a2af49ee86451c374a600579d3644c811cd12c0`  
**Docs package HEAD (pre-commit):** `85c94e5c2b1d120c4bcf8d9fe7deb94c628ff0b1`  
**CobraBench:** `prepared-not-run`  
**Official score:** **0.840**  
**Runtime behavior changed:** No

---

## 1. Strengths

1. **Cloud Linux Outcome A** with preserved diagnostics, cost, cleanup, and freeze package under `docs/releases/phase-3f/`.
2. **Pinned inference stack** (Python/torch/transformers/accelerate/bitsandbytes) with Phase 3G P1 runtime/dev split, torch pin, and container digest pin.
3. **Ops automation** for SSH bootstrap, env verify, provision preflight, cleanup verify, and P1 evidence hashing.
4. **Clear governance:** ADRs, evaluation policy, score/protocol integrity, Investigator boundary.
5. **VRAM envelope known** (~6 GiB peak) enabling honest SKU right-sizing guidance.
6. **Security hygiene:** no committed live secrets found; ignore rules for weights, bundles, and local cloud files.
7. **Phase 3G.5 package** adds architecture, operations, DR, security review, GPU matrix, and reproduction checklist.

---

## 2. Remaining technical debt

| Debt | Impact |
| --- | --- |
| CobraBench v0.2-rc2 never executed on qualified cloud runtime | Cannot claim bench-validated cloud performance |
| Only A40 SKU is smoke-`qualified`; L4/A5000 are candidates | Cost optimization blocked until abbreviated smoke |
| Windows / WSL paths failed or unavailable earlier | Cloud remains the only qualified Linux path |
| Supply-chain: version pins without full wheel hash lockfile enforcement in CI | Reproducibility relies on operator discipline |
| Historical lock hash BOM / encoding edge cases | Hash compare fragility |
| Phase 3F scripts still underscore-prefixed / semi-manual export | Higher operator skill requirement |
| No rehearsed DR drill on a blank machine | DR guide unproven in practice |
| Training/serving intentionally absent | Not debt for lab mission; gap if “product prod” is mis-scoped |

---

## 3. Operational risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Forgotten GPU pod left running | High $ | Cleanup script + checklist + ceiling |
| SSH blocked after create | Medium time/$ | `phase3g_ssh_bootstrap.py` |
| Overlay disk full | High session fail | `/workspace` mandate |
| Silent dependency drift | High requal | `phase3g_verify_env.py` + pins |
| Treating smoke-qualified as deployable | High governance | Explicit candidate limitations |
| Diagnostics commit with sensitive text | Medium | Review policy (Security S4) |
| Provider price/SKU churn | Medium | Live price check; re-auth |

---

## 4. Documentation gaps (after 3G.5)

Closed by this phase: architecture workflows, ops manual, DR, security review, GPU matrix, one-page checklist, readiness report.

**Still thin / future:**

- Provider-agnostic IaC (intentionally not built)
- On-call / paging (N/A for lab)
- Formal RTO rehearsal record
- Multi-region failover playbooks
- End-user “Cobra Core product” runbooks (out of repo mission)

---

## 5. Recommended Priority 2 work

Aligned with `PHASE_3G_CLOUD_RUNTIME_OPTIMIZATION_ROADMAP.md` and readiness gaps:

1. **Abbreviated smoke on L4 and/or A5000** (authorized spend) → promote SKUs in GPU matrix.
2. **Idempotent first-boot provision script** on `/workspace` (pins unchanged).
3. **CI job** for lock/pin/hash verification (no GPU).
4. **Wheel/hash pinning** or `pip` hash-checking mode for runtime requirements.
5. **Normalize evidence hash encoding** (BOM) and candidate schema validators.
6. **DR tabletop or blank-machine drill** with signed checklist evidence.
7. Only under **separate authorization:** controlled CobraBench v0.2-rc2 on locked runtime (not part of 3G.5).

---

## 6. Estimated production readiness percentage

### Definition used

**“Production readiness” for Cobra Core Model Lab** = ability to *reliably, safely, and reproducibly* operate the smoke-qualified cloud Linux runtime, preserve evidence, control cost/secrets, and hand off to another engineer — **not** public model serving or Investigator production.

### Score: **62%**

| Factor | Weight | Score | Notes |
| --- | ---: | ---: | --- |
| Qualified runtime existence | 20 | 18 | Outcome A on A40 |
| Reproducibility pins/docs | 20 | 16 | Strong pins + 3G.5 docs; SKU matrix partly untested |
| Ops automation & cleanup | 15 | 12 | P1 scripts exist; still semi-manual transfer |
| Evidence & governance | 15 | 13 | Freeze + ADRs + score integrity |
| Security posture | 10 | 8 | No critical secrets; process risks remain |
| Cost/SKU efficiency | 10 | 5 | A40 oversized; cheaper SKUs not smoke-proven |
| Benchmark-on-runtime | 10 | 2 | `prepared-not-run` |
| DR proven | 0 (folded) | — | Documented but not rehearsed → capped ops score |

**Interpretation:** Suitable for **controlled lab re-qualification and evidence-preserving ops**. Not ready to claim product production deployment or official cloud CobraBench results.

---

## 7. Integrity statement

- No model / prompt / inference / dependency version changes in Phase 3G.5.
- No benchmark execution; no training; no deployment; no cloud resource creation for this review.
- Official score remains **0.840**.
- CobraBench remains **prepared-not-run**.
- Runtime requalification **not required** for documentation-only 3G.5.

---

## 8. Package index

| Package | Path |
| --- | --- |
| Architecture | `docs/architecture/` |
| Operations | `docs/operations/` |
| Disaster recovery | `docs/disaster-recovery/` |
| Security review | `docs/security/SECURITY_REVIEW.md` |
| GPU matrix | `docs/runtime/GPU_COMPATIBILITY.md` |
| This report | `docs/PRODUCTION_READINESS_REPORT.md` |
