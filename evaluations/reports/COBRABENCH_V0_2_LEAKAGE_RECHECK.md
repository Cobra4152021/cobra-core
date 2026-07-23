# CobraBench v0.2 Leakage and Structural Diversity Recheck

**Phase:** 2H  
**rc1 tree hash verified:** `3c8cdc467183cf10567bcfe6f398258e894e5f979a54293d17ab2cb2c9e52b10`

## Checks

| Check | Result |
| --- | --- |
| Exact duplicate case_id / title | Pass |
| Near-duplicate titles (Jaccard ≥ 0.6) | One pair: cb2-019 vs cb2-034 (related but different categories/tasks) |
| Answer-cue phrases in prompts | None found |
| v0.1 ID collision | None (`cb2-` vs `cb-`) |
| Rubric leakage in user prompts | None |
| Source-key leakage of gold answers | None |

## Synthetic pattern repetition

| Pattern | Observation | Severity |
| --- | --- | --- |
| Shared system prompt | All investigation-style cases | D1 (by design) |
| Date clustering | 2026-01-01, 2026-04-18, 2026-05-01 recur | D2H-011 / D1 |
| S1/S2/S3 key scheme | Universal | Expected |
| Contradiction title cues (rc1) | Several titles named the conflict type | D2 → fixed in rc2 |
| Source title “UTC log” (rc1) | Cue in model-visible title | D3 → fixed in rc2 |

## Contamination status

All 46 cases remain synthetic, internally authored, `exclude_from_future_training_corpora`.  
No private evidence. No substantial copyrighted text.

## Conclusion

No contamination blocking release-candidate work. Structural repetition reduces diversity but is not contamination. Cueing issues addressed in **rc2**.
