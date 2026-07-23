# KC-001 — Benchmark Lab Integration Plan

**Do not implement the production adapter in this phase.**

Cobra Computer already has Benchmark Lab (queue, DO coordinator, weekly smoke, leaderboards, RBAC). Future Cobra Core Vision builds should plug in as a **first-party provider**, not via external VLM APIs.

---

## Proposed provider registration

| Field | Value |
|-------|--------|
| Provider name | `cobra_core` |
| Selection ID | `cobra-core-vision` |
| Versioned checkpoint ID | `cobra-core-vision@<gitsha>+<ckpt>` |
| Availability | `experimental` until KC-002+ gates pass |
| Endpoint | Private GPU Worker / HTTP sidecar (not askcobra public by default) |

---

## Suites

| Suite | Purpose |
|-------|---------|
| `vision-smoke` | 10–20 multimodal prompts from `eval/kc001` |
| `text-regression` | Preserved T1–T5 (+ expanded) against vision build **without** images |
| `vision-dependence` | Correct / wrong / blank / noise / none image matrix |
| `full` | Deferred — large VQA only after legal data clearance |

---

## Operational mapping

| Benchmark Lab concept | Cobra Core Vision |
|-----------------------|-------------------|
| Provider adapter | New adapter implementing existing chat-completions-like interface |
| Failure class | Reuse infra vs quality taxonomy |
| Cost accounting | GPU-seconds × rate card + token estimates |
| Timeout | Hard cancel + PARTIAL rules already in lab |
| Artifact retention | Store generations + image hashes (not necessarily raw pixels) |
| Health | `/healthz` on GPU endpoint before queue lease |

---

## Gate before production listing

1. Native vision definition checks green on **real** GPT-OSS weights  
2. Image-dependence pass  
3. Text regression within tolerance  
4. License status **A/B** for shipped checkpoint  
5. Security limits enforced  
6. Explicit product approval (separate from KC-001)

---

## Explicit non-actions (KC-001)

- No changes to `cobracomputer` worker routing  
- No weekly scheduler inclusion  
- No leaderboard pollution with unverified checkpoints  
