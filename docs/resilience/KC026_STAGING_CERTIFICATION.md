# KC-026 — RRF Staging Certification

**Status:** Certified for staging  
**Branch:** `kc-026-reliability-resilience`  
**Base:** `216fae3` (`kc-025-isf-staging-cert`)  
**Feature commit:** `ab1975e7eca8ce8f018803201bd0b6ea4b0206b7`  
**Certification tag:** `kc-026-rrf-staging-cert` (docs commit + feature)  
**Production:** disabled — not merged  

## Artifact

| Item | Value |
|------|--------|
| Image tag | `v0.9.0-rc1-ab1975e7eca8` |
| Image digest | `sha256:5ae73eb0ff1062265a2e4b4ed2acf5a109247fcf8859af185ba367876871b5cf` |
| Edge build | `kc026-edge-20260725a` |
| Staging URL | `https://cobra-core-staging.cobra4152020.workers.dev` |
| Final config | `RRF=true`, `ISF=true`, `AIR=true`, `CIAL_PROFILE=default`, `CIAL_LIVE_PROVIDER_ENABLED=false` |

## Local (Phase 1)

| Check | Result |
|-------|--------|
| Full pytest | 421 passed, 3 skipped, 6 deselected |
| RRF unit + fault injection (`tests/test_rrf.py`) | PASS |
| ISF / AIR / CIAL / Protocol / approval regression | PASS |
| ruff / format / mypy | PASS (as run in Phase 1) |

## Staging phases

| Phase | Config | Workflow / evidence | Status |
|-------|--------|---------------------|--------|
| 2 Offline | RRF/ISF/AIR=true, live=false, suffix `kc026a` | [30181875627](https://github.com/Cobra4152021/cobra-core/actions/runs/30181875627) + harness 7/7 | PASS |
| 3 Live | research + live=true, suffix `kc026b` | [30181943425](https://github.com/Cobra4152021/cobra-core/actions/runs/30181943425) — 5 skills → openai → `pending_approval` | PASS |
| 4 Fault cert | Deterministic `faults.py` + `tests/test_rrf.py` (no real credential mutation) | Local matrix 1–28 | PASS |
| 5 Governance | Computer `npm run kc018:approval` | 13/13 during live + rollback windows | PASS |
| 6 Soak | Offline mixed 10/25/50 | Harness (see `KC026_SOAK_RESULTS.md`) — 0 unexpected | PASS |
| 7 Live close | live=false, suffix `kc026c` | [30182087974](https://github.com/Cobra4152021/cobra-core/actions/runs/30182087974) + offline recheck | PASS |
| 8 Rollback | RRF=false (`kc026f`) then restore (`kc026g`) | [30182263686](https://github.com/Cobra4152021/cobra-core/actions/runs/30182263686) rollback 2/2; restore [30182313845](https://github.com/Cobra4152021/cobra-core/actions/runs/30182313845) offline 7/7 | PASS |

## Related deploys (same image SHA)

| Suffix | Run ID | Purpose |
|--------|--------|---------|
| kc026a | 30181875627 | Phase 2 offline |
| kc026b | 30181943425 | Phase 3 live |
| kc026c | 30182087974 | Phase 7 live close |
| kc026d | 30182129692 | Phase 8 first rollback attempt |
| kc026e | 30182198798 | Interim restore |
| kc026f | 30182263686 | Phase 8 rollback re-verify |
| kc026g | 30182313845 | Final certified restore (RRF on, live off) |

## Known limitations

- Circuit breakers are in-process (not distributed across container replicas).
- Cost uses versioned static prices (`kc026-v1`); no live pricing APIs.
- Mock RRF path returns schema-shaped JSON (not free-form mock text).
- Only mock + OpenAI registered; vision never falls back to text-only mock.

## Production recommendation

Keep production disabled. Do not merge until an explicit production readiness milestone. Staging may remain on RRF with live gate closed.
