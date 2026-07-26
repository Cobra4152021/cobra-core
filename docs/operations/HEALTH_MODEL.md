# Health Model

## Status values

| Status | Meaning |
|--------|---------|
| `healthy` | Component available for intended operation |
| `degraded` | Available with impaired capability |
| `maintenance` | Intentionally paused / maintenance mode |
| `offline` | Disabled or unreachable |

## Components

Computer, Cases, Workflow Engine, ISF, KEF, Evidence Vault, AIR, RRF, CIAL, Benchmark, Metrics, Audit.

## Overall rollup

1. Critical offline (`computer`, `isf`, `air`, `rrf`, `cial`, `metrics`, `audit`) → overall `offline`
2. Else any `maintenance` → overall `maintenance`
3. Else any `degraded` → overall `degraded`
4. Else `healthy`

Optional components (cases/workflows/vault/benchmark) may be offline without failing the whole system when flags are off.

## Transitions

Health transitions are audited and counted in `system_health` metrics.
