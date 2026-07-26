# KC-026 Soak Results

**Environment:** staging offline (`CIAL_LIVE_PROVIDER_ENABLED=false`, catalog `mock` only)  
**Harness:** `python scripts/kc026/staging_cert.py --soak N`  
**Image:** `v0.9.0-rc1-ab1975e7eca8`  
**Config:** `RRF=true`, `ISF=true`, `AIR=true`, `CIAL_PROFILE=default`  
**No OpenAI traffic** during soak  

## Mixed workload (harness)

Approximate mix: normal success, expected fail-closed capability miss, and other offline-safe paths. Provider transport faults are certified in unit tests, not against live OpenAI during soak.

## Results

| Stage | Total | Successes | Expected failures | Unexpected failures | avg ms | p50 ms | p95 ms |
|-------|-------|-----------|-------------------|---------------------|--------|--------|--------|
| 10 | 10 | 9 | 1 | 0 | 237.74 | 232.82 | 291.52 |
| 25 | 25 | 23 | 2 | 0 | 230.08 | 230.56 | 249.30 |
| 50 | 50 | 45 | 5 | 0 | 228.59 | 231.42 | 243.51 |

## Totals (10+25+50)

| Metric | Value |
|--------|-------|
| Logical executions | 85 |
| Successful executions | 77 |
| Expected failures | 8 |
| Unexpected failures | 0 |
| Duplicate proposals | 0 (governance + idempotency tests) |
| Governance failures | 0 |

## Notes

- Offline soak does not exercise live OpenAI retries; those are covered in Phase 3 (live skills) and Phase 4 (deterministic fault matrix).
- Audit completeness verified via `/rrf/audit` during Phase 2 offline checks.
