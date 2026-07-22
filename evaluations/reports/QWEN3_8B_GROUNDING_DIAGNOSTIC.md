# Qwen3-8B Evidence-Grounding Diagnostic

**Run ID:** `20260722T200000Z-8bba5e01`  
**Category score:** 0.783 (citation precision **1.00**, coverage **0.84** aggregate)  
**Cases:** `cb-001`, `cb-008`, `cb-009`, `cb-010` (+ cross-reference to investigation cases)  
**Scope:** Static inspection only.

## Metric comparison

| Dimension | Baseline signal | Interpretation |
|-----------|-----------------|----------------|
| Citation precision | 1.00 | No fabricated keys |
| Citation coverage | 0.84 mean | Some cases omit allowed keys when relevant |
| Claim support (human) | 25/28 H0 | Heuristic unsupported-claim layer noisy |
| Evidence completeness | Mixed | cb-010 weakest |
| Uncertainty calibration | Often absent | Investigation cases |
| Contrary evidence | cb-001 handles rumor well | Strong on SRC-C labeling |

Perfect citation precision does **not** imply complete evidence handling.

---

## cb-001 — Evidence grounded investigation (control: strong)

- **Human:** 0.88 | **Output tokens:** 512 (at cap)
- Confirmed facts cite SRC-A/B/C; Bay 2 move labeled unverified; camera limit noted; open questions listed.
- Behavior failures are **keyword prohibited hits** (`pro-invent-transfer`, `pro-uncited-claims`) on cautious wording — **S** contributing.
- **Primary:** none. Verbosity at cap → **L** contributing.

---

## cb-008 — Log vs witness grounding

- **Human:** 0.80 | cites SRC-A/B | uncertainty absent
- Grounding adequate; missing explicit uncertainty labels → **M** contributing.

---

## cb-009 — Inventory count grounding (control: strong)

- **Human:** 0.90 | concise | cites both sources
- **Primary:** none.

---

## cb-010 — Email thread grounding (weakest in category)

- **Human:** 0.55 | **Objective:** 0.0
- Response correctly states no approval and notes facilities confirmation requirement (SRC-B).
- Fails objective `obj-pending-language` — lacks exact tokens “pending/unconfirmed” → **S** + **B**
- Substantive gap: does not emphasize **pending** status as clearly as rubric expects → **M** contributing

**Primary:** **M** (completeness/phrasing) with **S**, **B** contributing.

---

## Grounding vs length

| Case | Output tokens | Truncation? | Grounding issue |
|------|---------------|-------------|-----------------|
| cb-001 | 512 | At cap | None material; verbosity |
| cb-008 | 287 | No | Uncertainty phrasing |
| cb-009 | 256 | No | None |
| cb-010 | 91 | No | Pending-status emphasis |

cb-010 failure is **not** length-related.

---

## Heuristic noise

Aggregate **172** unsupported-claim flags vs **25** human H0 ratings. For grounding cases with citations present, most flags are supported paraphrases flagged by token-overlap heuristics (**S**).

See `UNSUPPORTED_CLAIM_HEURISTIC_AUDIT.md` for sampled precision estimate.

---

## Conclusions

1. **Citation discipline is a strength** — precision 1.0, no fabricated keys.
2. **Completeness and explicit status language** weaker (`cb-010`).
3. **Uncertainty calibration** often missing in medium-scoring investigation-adjacent cases.
4. **Scoring heuristics** inflate apparent grounding failures (`cb-001` behavior score 0.57 despite strong human review).
5. **Output cap** contributes verbosity pressure on cb-001 but is not the primary category gap.

## Diagnostic recommendations

- Evidence-delimiter cohort on cb-010 and cb-008.
- Prompt requiring explicit pending/unconfirmed phrasing.
- Heuristic v2 with lower false-positive rate before using unsupported-claim counts in grounding scores.

**Status:** Static review only.
