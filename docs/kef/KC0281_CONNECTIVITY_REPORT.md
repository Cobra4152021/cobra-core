# KC-028.1 — Connectivity Report

**Branch:** `kc-0281-vault-connectivity-cert`  
**Base:** `7d1f439` (KC-028 PARTIAL)  
**Purpose:** Complete KC-028 by restoring Core → Evidence Vault reachability.  
**Production:** disabled. Do not merge.

## Root cause

Cloudflare Bot Fight Mode challenged outbound `urllib` requests from the Core container when the default Python User-Agent was used. Vault endpoints returned challenge HTML (or non-JSON bodies). The connector treated those as failures → **degraded** health and skill-path timeouts.

Secondary issue: container image rollouts required a new Durable Object instance name **and** `--containers-rollout=immediate`; otherwise staging could keep serving a prior image digest.

## Fix

1. Browser-compatible `User-Agent` + `Accept` via `vault_request_headers()` on all Vault calls.
2. Health requires HTTP 2xx **and** JSON body (challenge HTML → degraded).
3. Authenticated `GET /kef/diagnostics` instruments DNS → TLS → auth → health/search/file.
4. Deploy with fresh DO suffix + immediate container rollout.

## Connectivity status (post-fix)

| Step | Status |
|------|--------|
| DNS | ok |
| TLS (SNI) | ok (TLSv1.3) |
| Auth (`X-Hidden-Grid-Key`) | ok |
| Vault health | healthy |
| Search | ok |
| Metadata / content / chunk (`/api/file`) | ok |
| Evidence Vault connector registry | healthy |

## Workflow IDs

| Run | Purpose |
|-----|---------|
| 30185736153 | kc0281a first connectivity deploy |
| 30186205559 | kc0281b immediate rollout (cert green) |
| 30186465156 | Phase 9 rollback (KEF/Vault off) |
| 30186522856 | Restore Vault enabled (`kc0281c`) |

## Certification tag

`kc-028-kef-vault-staging-cert` — tags the KC-028 completion commit (KC-028.1 does not receive a separate architecture tag).
