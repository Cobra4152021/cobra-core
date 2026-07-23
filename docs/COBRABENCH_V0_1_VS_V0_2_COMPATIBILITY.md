# CobraBench v0.1 versus v0.2 Compatibility

## Summary

Historical **0.840** remains valid only under CobraBench **v0.1** and its original evaluator versions.
A future v0.2 / rc1 score must **not** be presented as direct improvement or decline without qualification.

## Why scores are not interchangeable

| Dimension | v0.1 | v0.2-rc1 |
| --- | --- | --- |
| Categories | 9 | 10 (adds uncertainty_calibration) |
| Weights | v0.1 table | v0.2 table (different) |
| Unsupported-claim evaluator | v1 (noisy) | v2 |
| Citation metrics | basic precision/coverage | precision + claim/evidence/contrary coverage |
| Contradiction | mostly collapsed | 10 submetrics |
| Evidence keys | SRC-* | S# source blocks (prospective standard) |
| Format scoring | mixed | semantic vs exact separated |
| Parsers | limited | strict + tolerant |
| Prompt standard | legacy | versioned templates |

## No conversion formula

No statistically supported conversion between v0.1 and v0.2 overall scores is provided.
Do not invent one.

## Reporting rules

* Always display benchmark version and evaluator versions.
* Keep v0.1 leaderboards separate from v0.2-rc1 diagnostics.
* Official Phase 2D baseline artifacts must not be overwritten by rc1 runs.
