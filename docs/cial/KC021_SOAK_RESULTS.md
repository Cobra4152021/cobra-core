# KC-021 — Soak Results

## Plan

Cost-controlled live soak after deploy approval:

| Stage | Requests | Notes |
|-------|----------|-------|
| 1 | 10 | smoke |
| 2 | 25 | stability |
| 3 | 50 | stop if budget/quota hit |

Stop immediately on: unexpected cost growth, malformed responses, auth leakage,
governance regression, audit failure, revision mismatch.

## Metrics to collect

- success rate
- avg / p50 / p95 latency
- retry rate
- timeout rate
- provider errors
- malformed responses
- estimated tokens / cost (configured metadata only)

## Results

**Not executed yet** — awaiting explicit staging deployment approval and live
enablement.

| Stage | Success % | Avg ms | p50 | p95 | Retries | Timeouts | Errors | Est. tokens | Est. cost |
|-------|-----------|--------|-----|-----|---------|----------|--------|-------------|-----------|
| 10 | — | — | — | — | — | — | — | — | — |
| 25 | — | — | — | — | — | — | — | — | — |
| 50 | — | — | — | — | — | — | — | — | — |
