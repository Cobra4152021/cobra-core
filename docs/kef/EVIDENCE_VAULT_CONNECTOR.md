# Evidence Vault Connector

**Module:** `src/cobra_core/kef/connectors/evidence_vault.py`  
**Transport:** `src/cobra_core/kef/vault_http.py`

## Operations

| Method | Vault API |
|--------|-----------|
| `health()` | `GET /api/r2-health` (TTL-cached) |
| `lookup` / `read` / `metadata` | `GET /api/file?manifestKey=` |
| `search` | `GET /api/search` or `/api/evidence-search` when `case_id` set |

## Configuration

| Env | Role |
|-----|------|
| `KEF_EVIDENCE_VAULT_ENABLED` | Master switch |
| `KEF_EVIDENCE_VAULT_BASE_URL` | HTTPS Computer staging URL |
| `KEF_EVIDENCE_VAULT_AUTH_TOKEN` | Secret read credential |
| `KEF_EVIDENCE_VAULT_TIMEOUT_MS` | Per-request timeout |
| `KEF_EVIDENCE_VAULT_MAX_RESULTS` | Cap |
| `KEF_EVIDENCE_VAULT_REQUIRE_TLS` | Fail closed unless https |
| `KEF_ALLOW_REQUEST_SEED` | Must be `false` in staging cert |

## Resilience

- Dependency class: `evidence_connector` (circuit key `evidence_vault`)
- Max 2 attempts; retry only timeout/429/500
- No retry on 401/403
- No fallback to MemoryConnector unless `KEF_ALLOW_REQUEST_SEED=true` (tests only)

## Deterministic tests

`DeterministicVaultAdapter` simulates success, auth failures, timeouts, mismatch, duplicates, oversized content.
