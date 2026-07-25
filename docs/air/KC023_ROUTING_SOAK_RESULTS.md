# KC-023 — Controlled Routing Soak Results

**Commit:** `2b92b4194507`  
**Live gate:** open (`CIAL_PROFILE=research`, `CIAL_LIVE_PROVIDER_ENABLED=true`)  
**Workflow:** [30178772077](https://github.com/Cobra4152021/cobra-core/actions/runs/30178772077)  
**Workload:** 40% text+offline→mock, 30% reasoning→openai, 20% reasoning+vision→openai, 10% unsupported→fail-closed  
**Method:** authenticated `POST /air/route` (no prompts logged)

## Results

| Stage | N | Successes | Expected failures | Unexpected failures | mock | openai | avg ms | p50 | p95 | audit_ok |
|-------|---|-----------|-------------------|---------------------|------|--------|--------|-----|-----|----------|
| 1 | 10 | 10 | 1 | **0** | 4 | 5 | 85.2 | 77.8 | 97.5 | 8 |
| 2 | 25 | 25 | 2 | **0** | 12 | 11 | 77.4 | 77.0 | 94.1 | 23 |
| 3 | 50 | 50 | 5 | **0** | 20 | 25 | 74.2 | 75.5 | 90.8 | 45 |

Models: `cobra-core-qwen3-8b` (mock), `gpt-5.4-mini` (openai).

## Stop conditions

None triggered (no credential leakage, selection mismatch, unexpected fallback, governance regression, abnormal cost, or rollback failure).

## Notes

- Token usage / estimated USD cost not billed here; soak used routing dry-run only (no inference tokens except separate live E2E `pong`).
- Audit completeness on stage 3 was 45/50 via correlation lookup (bounded in-memory log); selection outcomes remained correct.
- Concurrency/quota gates not bypassed.
