# RRF Retry Policy

- Default `RRF_MAX_ATTEMPTS=2` (1 initial + 1 retry)
- No recursive loops
- Backoff: exponential with full jitter; honor `Retry-After` when within remaining deadline
- Defaults: initial 250ms, max 2s, request deadline 30s
- Cancellation stops further retries
