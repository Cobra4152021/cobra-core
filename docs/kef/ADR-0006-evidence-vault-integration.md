# ADR-0006 — Evidence Vault Integration (KC-028)

## Status

Accepted for staging certification

## Context

KC-027 introduced KEF with an Evidence Vault stub. Investigation Skills need read-only access to the Computer Evidence Vault without ISF/AIR/RRF/CIAL coupling to R2/D1.

## Decision

Replace the stub with a read-only `EvidenceVaultConnector` that calls Computer Vault HTTP:

- `GET /api/r2-health`, `/api/file`, `/api/extract`, `/api/search`, `/api/evidence-search`
- Auth: staging service credential via `X-Hidden-Grid-Key` (`KEF_EVIDENCE_VAULT_AUTH_TOKEN`)
- `KEF_ALLOW_REQUEST_SEED=false` by default (no trusted body injection)
- Distinct connector circuit/retry from provider RRF state
- Citation provenance maps `EV-xxx` → vault source IDs

## Consequences

- Computer remains storage owner; KEF remains the evidence gateway
- No Core writes to Vault
- Staging cert requires vault token secret + HTTPS base URL
- Production remains disabled
