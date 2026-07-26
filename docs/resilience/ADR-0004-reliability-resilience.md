# ADR-0004 — Reliability & Resilience Framework (RRF)

## Status

Accepted (KC-026 staging certification)

## Context

ISF → AIR → CIAL provider calls need bounded retries, circuit breaking, constrained fallback, and budget protection without bypassing human approval or silently downgrading capabilities.

## Decision

Insert a provider-neutral **Resilience Execution Layer** after AIR selects a route:

`Computer → ISF → AIR → RRF → CIAL → Provider → structured result → pending_approval`

AIR remains the sole router. RRF executes the chosen route safely.

## Consequences

- Retries capped (default 2 attempts); schema repair remains ≤1; total provider calls ≤3
- Vision skills never fall back to text-only mock
- Offline fallback only when manifest/policy/live-gate allow
- Successful results always `pending_approval`
- `RRF_ENABLED=false` restores the KC-025 path
