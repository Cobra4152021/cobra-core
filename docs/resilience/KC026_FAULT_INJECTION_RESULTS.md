# KC-026 Fault Injection Results

**Harness:** `src/cobra_core/resilience/faults.py` + `tests/test_rrf.py`  
**Environment:** local unit / deterministic transports only  
**Constraint:** No deliberate mutation of real API credentials  

## Matrix coverage

| # | Scenario | Result |
|---|----------|--------|
| 1 | Timeout retries once, then succeeds | PASS |
| 2 | Timeout retries once, then fails typed | PASS |
| 3 | Authentication failure not retried | PASS |
| 4 | Authorization failure not retried | PASS |
| 5 | Rate limit honors bounded Retry-After | PASS |
| 6 | Excessive-After beyond deadline fails without oversleep | PASS |
| 7 | Five qualifying failures open circuit | PASS |
| 8 | Open circuit blocks new calls | PASS |
| 9 | Open → half-open after policy duration | PASS |
| 10 | Successful probes close circuit | PASS |
| 11 | Failed half-open probe reopens | PASS |
| 12 | Vision skill never falls back to text-only mock | PASS |
| 13 | Offline-compatible summary may fallback to mock | PASS |
| 14 | Policy exclusion prevents fallback | PASS |
| 15 | Closed live gate prevents fallback to OpenAI | PASS |
| 16 | Budget checked before every attempt | PASS |
| 17 | Execution stops when budget exhausted | PASS |
| 18 | Total provider-call ceiling enforced | PASS |
| 19 | Schema repair limited to one attempt | PASS |
| 20 | Retry + repair does not exceed call ceiling | PASS |
| 21 | Cancellation stops retry and fallback | PASS |
| 22 | Cancellation does not open circuit | PASS |
| 23 | Idempotent replay does not duplicate proposals | PASS |
| 24 | Revision change creates distinct execution | PASS |
| 25 | Successful results remain `pending_approval` | PASS |
| 26 | Audit contains complete attempt history | PASS |
| 27 | Metrics use bounded labels only | PASS |
| 28 | `RRF_ENABLED=false` restores KC-025 path | PASS |

## Staging note (Phase 4)

Controlled staging fault certification uses the same deterministic adapter categories. Live provider credentials were not corrupted for testing.
