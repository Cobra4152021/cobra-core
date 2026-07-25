# KC-021 — Soak Results

## Plan

Cost-controlled live soak after research activation:

| Stage | Requests | Notes |
|-------|----------|-------|
| 1 | 10 | smoke |
| 2 | 25 | stability |
| 3 | 50 | stop if budget/quota hit |

Stop immediately on: unexpected cost growth, malformed responses, auth leakage,
governance regression, audit failure, revision mismatch.

## Guardrails in force

- `CIAL_LIVE_MAX_CONCURRENT=1`
- `CIAL_LIVE_MAX_INPUT_CHARS=8000`
- `CIAL_LIVE_MAX_OUTPUT_TOKENS=2048`
- `CIAL_LIVE_DAILY_REQUEST_QUOTA=120`
- `CIAL_LIVE_DAILY_COST_CEILING=5.00`
- Kill switch off; `APP_ENV=staging` only
- Soak used `max_tokens=16` (maps to `max_completion_tokens` for gpt-5.4-mini)

## Results

Executed 2026-07-25 after Phase 3–4 live path green. Endpoint:
`https://cobra-core-staging.cobra4152020.workers.dev` (Bearer + org header).

| Stage | Success % | Avg ms | p50 | p95 | Retries | Timeouts | Errors | Est. tokens | Notes |
|-------|-----------|--------|-----|-----|---------|----------|--------|-------------|-------|
| 10 | 100 | 709 | 671 | 814 | 0 | 0 | 0 | 230 | PASS |
| 25 | 100 | 606 | 580 | 715 | 0 | 0 | 0 | 575 | PASS |
| 50 | 100 | 696 | 591 | 738 | 0 | 0 | 0 | 1150 | PASS |

- Mock regressions: 0
- Auth / credential leakage in responses: none observed
- Revision mismatch: none (`ec400d83…` held)
- Abnormal cost growth: not observed (small completions)

## Status

**PASS** — soak complete; proceeded to Phase 6 rollback.
