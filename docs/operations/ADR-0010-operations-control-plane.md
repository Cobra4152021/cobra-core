# ADR-0010 — Operations Control Plane (OCP)

## Status

Accepted (KC-032)

## Context

Cobra Core now includes AIR, ISF, RRF, KEF, Evidence Vault connectivity, and the Investigation Benchmark framework. Operators need visibility and safe administrative controls without changing investigation routing, workflows, or provider selection.

## Decision

Add `cobra_core.operations` as an Operations Control Plane:

```
Administrator → OCP → Cases / Workflows / ISF / KEF / Vault / AIR / RRF / Benchmark / Metrics / Audit
```

OCP owns:

- Component health aggregation (`healthy|degraded|maintenance|offline`)
- Versioned feature flags with audit
- System-wide read-only mode
- Maintenance enter/drain/exit
- Daily quotas (warning / soft / hard)
- Usage snapshots
- Informational alerts
- Authenticated status APIs under `/operations/*`

OCP does **not** own web UI, notifications, auto-scaling, Kubernetes, AI ops, or production enablement.

## Consequences

- Admins can freeze writes (`READ_ONLY_MODE`) and enter maintenance without changing AIR/CIAL logic
- Quotas and alerts are informational gates for callers; OCP does not silently rewrite investigation outcomes
- Cases/Workflows report `offline` until their feature flags are enabled (KC-029/031 not required for OCP)
- Production remains disabled; no automatic merge
