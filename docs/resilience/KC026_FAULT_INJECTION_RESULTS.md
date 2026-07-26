# KC-026 Fault Injection Results

Deterministic harness: `src/cobra_core/resilience/faults.py` + `tests/test_rrf.py`.

Covered: timeout retry success/fail, auth/authz no-retry, rate-limit Retry-After, circuit open/half-open/close/reopen, vision no-fallback, offline summary fallback, budget pre-check, call ceiling, schema repair once, cancellation, idempotency, metrics labels, `RRF_ENABLED=false` KC-025 path.

No real credential mutation.
