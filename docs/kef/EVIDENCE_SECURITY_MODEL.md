# Evidence Security Model

## Authentication

Core → Vault uses a least-privilege staging read credential (`KEF_EVIDENCE_VAULT_AUTH_TOKEN`), never logged or audited.

## Authorization

1. Vault enforces org/RBAC on its API
2. KEF independently applies `EvidencePermissions` + `Principal` (role, classification ceiling)
3. Denied items never enter ISF/provider context
4. Incomplete permission metadata fails closed via deny/quarantine flags

## Public errors

Safe codes only (`missing_required_evidence`, `evidence_access_denied`, connector unavailable). No titles/excerpts of denied items in public errors.
