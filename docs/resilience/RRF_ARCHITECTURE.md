# RRF Architecture

Flow: `Computer → ISF → AIR → ResilienceExecutor → CIAL.complete_on_route → Provider`

Package: `src/cobra_core/resilience/`

| Module | Role |
|--------|------|
| `executor.py` | Orchestrates attempts, repair, fallback |
| `circuit_breaker.py` | closed / open / half_open |
| `retry.py` / `backoff.py` | Bounded retry + jitter |
| `fallback.py` | Capability-preserving fallback |
| `budget.py` / `prices.py` | Pre-call cost gates |
| `idempotency.py` | One logical proposal per execution id |
| `faults.py` | Deterministic fault injection |
| `audit.py` / `metrics.py` | Safe observability |

Gate: `RRF_ENABLED` (default true). When false, ISF uses the KC-025 path.
