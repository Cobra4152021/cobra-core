# KC-028 — KEF + Evidence Vault Staging Certification

**Branch:** `kc-028-evidence-vault-kef-cert`  
**Base:** `275395d`  
**Feature commits:** `3abf1c5` … `1257fa3` (+ harness fixes)  
**Suggested tag:** `kc-028-kef-vault-staging-cert` — **not created** (staging blocker)  
**Production:** disabled  

## Artifacts

| Item | Value |
|------|--------|
| Image family | `v0.9.0-rc1-<sha>` (see workflow runs) |
| Edge build | `kc028-edge-20260726a` |
| Staging Core | `https://cobra-core-staging.cobra4152020.workers.dev` |
| Staging Vault | `https://hidden-grid-os-staging.cobra4152020.workers.dev` |
| Final intended config | KEF=true, Vault=true, seed=false, RRF/ISF/AIR=true, live=false |

## Workflow runs (selected)

| Suffix | Run ID | Purpose |
|--------|--------|---------|
| kc028a | 30184048032 | First vault-enabled deploy (token missing) |
| kc028b | 30184173039 | Token secret bound |
| kc028c | 30184299343 | Non-blocking /health |
| kc028d | 30184509486 | Transport harden |
| kc028e | 30184699536 | KEF edge proxy + fixtures seeded |

## Phase results

| Phase | Result | Notes |
|-------|--------|-------|
| 1 Local | **PASS** | Full pytest green; `tests/test_kef_vault.py` matrix |
| 2 Offline staging | **PARTIAL** | Gate/status/metrics/missing-evidence PASS; Vault health **degraded**; Core→Vault lookups hang/timeout from Containers |
| 3–8 | **BLOCKED** | Depend on healthy Core→Vault retrieval |
| 9 Rollback | Not run end-to-end | Local `KEF_ENABLED=false` path covered by unit tests |

## Named blockers

1. **Core Container → Evidence Vault HTTP** returns non-healthy (`degraded`) and skill executes that require Vault lookup time out. Direct Vault calls from the cert workstation with the same staging key succeed (`/api/r2-health` 200, uploads OK).
2. Until outbound Vault calls succeed from the Core container network path (or a Worker service-binding proxy is added), end-to-end Vault-grounded skill certification cannot complete.

## Credential scope

`KEF_EVIDENCE_VAULT_AUTH_TOKEN` = staging Computer maintenance read key (`X-Hidden-Grid-Key`), least-privilege relative to session auth; never logged.

## Production recommendation

Do not enable production. Do not merge until Core→Vault connectivity is certified healthy and Phases 3–9 pass.
