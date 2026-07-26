# KC-028.1 — Network Analysis

## Path under test

```
Cobra Core Container
  → public HTTPS
  → hidden-grid-os-staging.cobra4152020.workers.dev
  → Evidence Vault APIs
```

## Validations

| Layer | Result | Notes |
|-------|--------|-------|
| DNS IPv4 | ok | 2 addresses resolved |
| DNS IPv6 | ok | 2 addresses resolved |
| TLS / SNI | ok | TLSv1.3 to Vault hostname |
| HTTP | ok | JSON responses after UA fix |
| Timeouts | ok | `KEF_EVIDENCE_VAULT_TIMEOUT_MS=10000` |
| Retries | ok | connector `vault_max_attempts` + RRF breaker (unit-tested) |
| Connection pooling | N/A | urllib per-request; acceptable for staging cert |

## Failure mode (before)

| Symptom | Cause |
|---------|--------|
| Vault health `degraded` | Challenge / non-JSON body |
| `/isf/execute` Vault lookups timeout | Same egress path |
| Workstation Vault calls succeed | Cert harness already used browser-like UA |

## Configuration (staging)

- `KEF_ENABLED=true`
- `KEF_EVIDENCE_VAULT_ENABLED=true`
- `KEF_ALLOW_REQUEST_SEED=false`
- `CIAL_LIVE_PROVIDER_ENABLED=false`
- Vault base: `https://hidden-grid-os-staging.cobra4152020.workers.dev`
- Auth secret: `KEF_EVIDENCE_VAULT_AUTH_TOKEN` → header `X-Hidden-Grid-Key` (never logged)

## Known limitations

- Public HTTPS topology only (no service binding yet).
- Case-scoped `/api/evidence-search` is not used as a global diagnostics probe (requires case id).
- Container DO envVars freeze at construction — bump instance suffix after secret/var changes.
