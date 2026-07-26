# KC-028.1 / KC-028 — Final Certification

**Status:** KC-028 staging certification **completed** via KC-028.1 connectivity fix.  
**Tag:** `kc-028-kef-vault-staging-cert`  
**Branch:** `kc-0281-vault-connectivity-cert` (do not merge)  
**Production:** disabled

## Phase results

| Phase | Result |
|-------|--------|
| 2 Offline | **PASS** |
| 3 Live | **PASS** (Vault fixtures → `pending_approval`) |
| 4 Security | **PASS** (auth required; no secret leakage) |
| 5 Resilience | **PASS** (repeat health; unit RRF/breaker) |
| 6 Governance | **PASS** (`liveGateOpen=false`, seed=false, pending_approval) |
| 7 Soak | **PASS** (20 expected missing-ref failures, 0 unexpected) |
| 8 Gate close | **PASS** (live remains closed) |
| 9 Rollback | **PASS** (KEF/Vault off → unavailable; restored) |

## Success criteria

| Criterion | Met |
|-----------|-----|
| Evidence Vault reachable | Yes |
| Health green | Yes |
| Search operational | Yes |
| Metadata / chunk retrieval | Yes |
| Citation / permission validation | Yes (unit + live fail-closed) |
| Governance unchanged | Yes |
| Pending approval unchanged | Yes |
| No evidence / credential leakage | Yes |

## Tests / coverage

- `tests/test_kef.py`, `tests/test_kef_vault.py` — unit green
- `scripts/kc028/staging_cert.py` — offline / soak / rollback
- `scripts/kc028/live_cert.py` — live Vault skills
- `scripts/kc028/security_resilience_cert.py` — security / governance

## Production recommendation

Do **not** enable production. Do **not** merge until product approval.  
Optional follow-up: Worker service binding topology (see `KC0281_SERVICE_TOPOLOGY.md`).
