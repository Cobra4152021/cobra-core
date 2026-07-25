# KC-025 — ISF Staging Certification

**Suggested tag:** `kc-025-isf-staging-cert` (only if all mandatory phases pass)  
**Branch:** `kc-025-isf-staging-cert`  
**Base commit:** `dde59ec`  
**Prior tags:** do not modify (`kc-023-air-staging-cert`, etc.)  
**Production:** remains disabled  

## Local verification (pre-deploy)

| Check | Result |
|-------|--------|
| ISF unit + KC-025 tests | PASS |
| Full pytest suite | PASS |
| ruff / format / mypy (isf) | PASS |
| ISF coverage | ~87% |

## Staging phases

| Phase | Config | Status |
|-------|--------|--------|
| 5 Offline | AIR=true, ISF=true, profile=default, live=false | pending |
| 6 Live | profile=research, live=true | pending |
| 7 Governance | Computer `kc018:approval` | pending |
| 8 Audit | `/isf/audit` fields | pending |
| 9 Telemetry | `/isf/metrics` + Prometheus | pending |
| 10 Soak | 10 / 25 / 50 | pending |
| 11 Live gate close | live=false, ISF=true | pending |
| 12 Rollback | ISF=false then restore | pending |

## Workflow / image

| Field | Value |
|-------|-------|
| Workflow run IDs | _pending_ |
| Image tag | _pending_ |
| Image digest | _pending_ |
| Worker / container | `staging-rc1-kc025a` (+ bumps) |

## Production recommendation

**Do not enable in production.** Staging-only certification of Computer → ISF → AIR → CIAL with human approval.
