# KC-028.1 — Latency Results

Measurements from Core container diagnostics and live skill cert harness (staging).

## Diagnostics step latencies (representative)

| Step | ms |
|------|-----|
| DNS | 3 |
| TLS | 40 |
| Health | 126–561 |
| Auth (health re-probe) | ~126 |
| Search | 3200–3900 |
| Metadata (`/api/file`) | 138 |
| Content (`/api/file`) | 165 |
| Chunk (`/api/file`) | 143 |
| **Overall diagnostics** | **~3800–4500** |

## Live Vault-backed skills (pending_approval)

| Metric | Before (KC-028 blocked) | After (KC-028.1) |
|--------|-------------------------|------------------|
| Vault health | degraded / timeout | healthy |
| Skill path | timeout / fail | pending_approval |
| Avg skill latency | N/A (blocked) | ~490–530 ms |
| p50 | N/A | ~460–497 ms |
| p95 | N/A | ~500–655 ms |

## Soak (missing-ref expected failures)

| Metric | Value |
|--------|-------|
| N | 20 |
| Unexpected failures | 0 |
| Expected missing_evidence | 20 |
| Avg latency | ~313 ms |
| p50 | ~308 ms |
| p95 | ~337 ms |

## Percentile summary (live skills, n=5)

| Percentile | ms |
|------------|-----|
| p50 | ~461 |
| p95 | ~655 |
| avg | ~531 |
