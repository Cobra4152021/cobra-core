# Qwen3-8B Contradiction Diagnostic

**Run ID:** `20260722T200000Z-8bba5e01`  
**Cases:** `cb-002-contradictory-witness-statements`, `cb-018-schedule-contradiction`, `cb-019-metric-contradiction`  
**Category score:** 0.767  
**Scope:** Static inspection only.

## Capability separation

| Sub-capability | cb-002 | cb-018 | cb-019 |
|----------------|--------|--------|--------|
| **Detection** | Strong | Strong | Weak |
| **Explanation** | Strong | Strong | Weak |
| **Classification** | Strong (direct vs agreement) | Strong (time + owner) | Partial |
| **Resolution recommendations** | Absent (appropriate) | Absent (appropriate) | Absent |

Do not treat these as a single “contradiction score.”

---

## cb-002 — Contradictory witness statements

**Human score:** 0.85 | **Objective:** 1.0 | **Output tokens:** 512 (at cap)

### Detection

Response section “Direct Contradictions” lists: headcount (2 vs 3), device (tablet vs phone), exit direction (east stairwell vs west elevator), folder mention, Lab Room 3 entry timeline.

### Explanation

Each contradiction pairs witness positions with specifics. Agreement section correctly notes overlapping facts.

### Classification

Does not force reconciliation (`identified_conflict=True; forced_reconcile=False`). Uncertainty language minimal but acceptable for human H0.

### Format

Long markdown structure consumed tokens; not a contradiction reasoning failure.

**Primary weakness:** none material. Contributing: **L** (verbosity at cap), **S** (19 unsupported-claim heuristic flags, H0 human).

---

## cb-018 — Schedule contradiction

**Human score:** 0.90 | **Objective:** 1.0 | **Output tokens:** 282

### Detection

Identifies overlapping bookings 14:00–15:00 (Team Red) vs 14:30–16:00 (Team Blue) with `SRC-A` / `SRC-B` citations.

### Explanation

Separates time conflict and booking-owner discrepancy.

### Classification

Treats overlap as impossible without assuming calendar error — appropriate non-reconciliation.

**Primary weakness:** none material. Contributing: **S** (heuristic noise).

---

## cb-019 — Metric contradiction

**Human score:** 0.55 | **Objective:** 0.0 | **Output tokens:** 71

### Detection

Response text:

> The two dashboard snapshots do not agree… [SRC-A] reports 1,240… [SRC-B] reports 986… indicating a discrepancy.

Both values cited; disagreement stated. Human review: `identified_conflict=False` — reviewer wanted stronger **numerical** conflict articulation (delta, unit, date scope).

### Explanation gap

Does not compute difference (254 users), discuss measurement definition, or classify severity — shallow vs cb-018.

### Objective checker

`obj-both-values` failed on keywords `both`, `equivalent`, `disagreement` despite semantic disagreement — **S** parser brittleness.

### Classification

Treats as generic “discrepancy” not metric-definition conflict.

**Primary weakness:** **M** (explanation depth). Contributing: **S**.

---

## Cross-case findings

| Pattern | Evidence |
|---------|----------|
| Detection generally strong | cb-002, cb-018 human ≥ 0.85 |
| Explanation depth variable | cb-019 weakest |
| Forced reconciliation avoided | all three |
| Heuristic unsupported-claim noise | all three flagged; all H0 human |
| Token cap | cb-002 at 512 — may limit resolution recommendations, not detection |

## Recommended diagnostics

1. **Thinking-mode cohort** on cb-019 (+ control cb-018): measure numeric explanation improvement vs latency.
2. **Prompt cohort** requiring explicit delta calculation for metric conflicts.
3. **Scoring fix** for cb-019 objective keyword checks (prospective v0.2).

**Status:** Static review only — Not verified by reruns.
