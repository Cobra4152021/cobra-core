# KC-004B — Investigator Core Intelligence v0.1.0-alpha2

Modules under `cobra/src/investigator/`:

- `strategy.ts` — investigation strategy selection
- `evidenceQuality.ts` — evidence scores
- `hypotheses.ts` — competing hypotheses
- `missingEvidence.ts` — gap detection
- `confidence.ts` — separated confidence + readiness
- `review.ts` — publication checklist
- `metrics.ts` — run metrics
- Enhanced `planner.ts` / `report.ts`

Tests: 22/22 with CKE + KC-004 + KC-004B.

Worker mount: cobracomputer `kc-004-cobra-investigator`.
