# ADR-0014 — Public API & SDK Framework (PASF)

## Status

Accepted (KC-036)

## Context

External clients (mobile, web portals, third-party software, Cloudflare Marketplace, desktop, automation) need a stable integration surface. Internal modules should consume the same contracts where practical.

## Decision

Add `cobra_core.api` as PASF:

```
Client → Public REST API (/api/v1) → API Gateway → ISPF Authorization → Core subsystems
```

PASF owns:

- Versioned REST under `/api/v1/`
- Deterministic OpenAPI 3.1
- Reference Python + TypeScript SDKs
- Cursor pagination, per-org/client rate limits
- Standard error model
- API audit + metrics
- Reserved webhook event names (no delivery)

PASF does **not** own GraphQL, gRPC, streaming, webhook delivery, or production enablement.

## Consequences

- Breaking changes require `/api/v2/`
- Authentication reuses ISPF Bearer / API Client / Service principals
- Production remains disabled; no automatic merge
