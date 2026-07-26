# KC-026 — RRF Staging Certification

**Branch:** `kc-026-reliability-resilience`  
**Base:** `216fae3` (`kc-025-isf-staging-cert`)  
**Suggested tag:** `kc-026-rrf-staging-cert` (only if all phases pass)  
**Production:** disabled  

## Local (Phase 1)

| Check | Result |
|-------|--------|
| Full pytest | 421 passed, 3 skipped |
| RRF unit + fault injection | PASS |
| ISF/AIR/CIAL/Protocol regression | PASS |

## Staging phases

| Phase | Config | Status |
|-------|--------|--------|
| 2 Offline | RRF/ISF/AIR=true, live=false | pending |
| 3 Live | research + live=true | pending |
| 4 Fault cert | deterministic harness (local + staging audit) | local PASS |
| 5 Governance | `kc018:approval` | pending |
| 6 Soak | 10/25/50 | pending |
| 7 Live close | live=false | pending |
| 8 Rollback | RRF=false then restore | pending |

See companion `KC026_*_RESULTS.md` files for filled evidence after staging runs.
