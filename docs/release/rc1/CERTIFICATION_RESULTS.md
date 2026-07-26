# RC1 Certification Results — v1.0.0-rc1

**Date:** 2026-07-26  
**Branch:** `kc-038-release-candidate-1`  
**Commit:** `dcfc21b`  
**Tag:** `v1.0.0-rc1.kc038` (legacy `v1.0.0-rc1` already pointed at KC-011 and was not force-moved)  
**Offline pack:** PASS  
**Release approval:** **BLOCKED** (24h staging soak incomplete)

## Verdict

**PARTIAL — RC blocked by listed issues**

Blocking:

1. `phase_7_soak_24h_incomplete` — mandatory 24-hour staging soak not executed

## Regression summary

Executed pytest suites covering KC-021 → KC-037 surfaces:

- Protocol V1 RC1 controls + conformance
- AIR routing/telemetry
- ISF skills + KC-025
- RRF, KEF (+ vault unit)
- Benchmark, Operations
- PEF, ISPF, MOTF, PASF, PRHF
- RC1 certification pack

**Result:** all selected suites green (exit code 0).

## Compatibility summary

| Check | Result |
|-------|--------|
| OpenAPI 3.1 deterministic | PASS |
| OpenAPI checksum | `8c4573e3cfd22457b96f71edf0a54fefbb6ebd4aa9315108e4cf158b75741e4e` |
| SDK surface (Python) | PASS |
| Pagination / errors / auth / versioning / rate limits | PASS |
| Sample plugins load/enable/disable/reload | PASS |

## Security summary

| Check | Result |
|-------|--------|
| PRHF security review | PASS |
| Cross-org denial | PASS |
| `allow_cross_org=false` | PASS |
| Bearer required for protected API | PASS |
| Production enablement disabled | PASS |

## Performance summary (in-process `/api/v1/status`)

| N | errors | avg ms | p95 ms | elapsed s |
|---|--------|--------|--------|-----------|
| 100 | 0 | 0.055 | 0.079 | 0.16 |
| 500 | 0 | 0.055 | 0.090 | 0.77 |
| 1000 | 0 | 0.052 | 0.086 | 1.45 |
| 5000 | 0 | 0.045 | 0.067 | 6.31 |

Startup validation duration: ~0.0001 s (config path; offline).

## Recovery summary

| Check | Result |
|-------|--------|
| Startup validation | PASS |
| Migration dry-run | PASS |
| Migration apply + rollback | PASS |
| Backup + restore dry-run/apply | PASS |

## Soak

| Mode | Result |
|------|--------|
| Local timed soak (10s, 193 req, 0 errors) | PASS (evidence only) |
| 24h staging soak | **NOT COMPLETE** (blocking) |

Machine-readable full pack: `CERTIFICATION_RESULTS.json`.

## Release recommendation

1. Keep production disabled.
2. Deploy current freeze to staging.
3. Execute 24-hour soak; attach memory growth, latency drift, error count, audit completeness.
4. Re-run RC1 pack with soak evidence → promote to approved RC if clean.
5. Do not merge to production-bearing branches until soak clears.
