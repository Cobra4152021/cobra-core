# RC2 readiness smoke

**Status:** fail  
**Gate:** 3 — Smoke test  
**Crash:** Windows `0xC0000005` (ACCESS_VIOLATION) during weight load (~75% of 399 modules)

## Attempts

1. `max_memory={0:"9GiB","cpu":"18GiB"}` — crash during load; no generation.
2. One authorized environmental retry with `max_memory={0:"8GiB","cpu":"14GiB"}` after confirming free GPU memory — same crash at ~75%.

Further retries are prohibited without separate authorization.

## Consequence

Controlled CobraBench v0.2-rc2 execution is **blocked**. No benchmark cases were run. Official CobraBench v0.1 score **0.840** remains unchanged and authoritative for v0.1 only.
