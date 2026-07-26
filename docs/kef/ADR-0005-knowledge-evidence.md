# ADR-0005 — Knowledge & Evidence Framework (KEF)

## Status

Accepted (KC-027)

## Context

Investigation Skills need a single, fail-closed gateway for evidence. Computer must not access evidence stores directly. ISF must not depend on connector-native formats. Every conclusion must cite supporting evidence.

## Decision

Insert KEF between ISF and AIR:

```
Computer → ISF → KEF → AIR → RRF → CIAL → Provider → structured result → pending_approval
```

KEF owns retrieval, validation, normalization, ranking, deduplication, permission checks, and citations. AIR remains the router. RRF remains the resilience executor.

## Consequences

- Required evidence is validated before AIR/RRF/CIAL
- Connectors are storage-neutral (`memory`, `mock`, `evidence_vault` stub)
- Citations (`EV-001` …) attach to skill outputs
- `KEF_ENABLED=false` restores KC-025 type-gap checks
- No embeddings, OCR, or production vault integrations in KC-027
