# KC-026 Rollback Results

## Phase 8 — RRF off

**Config:**

```
RRF_ENABLED=false
ISF_ENABLED=true
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

| Item | Value |
|------|--------|
| Deploy | [30182263686](https://github.com/Cobra4152021/cobra-core/actions/runs/30182263686) suffix `kc026f` |
| Worker `/rrf-gate` | `"false"` |
| Harness | `python scripts/kc026/staging_cert.py --phase rollback` → **2/2 PASS** |
| Behavior | KC-025 execution path restored; RRF executor not invoked for ISF completes |
| Approval regression | 13/13 PASS during rollback window |

Earlier deploy `30182129692` (`kc026d`) was a first rollback attempt; re-verified on `kc026f` after health/`rrf-gate` consistency check.

## Restore — certified resting state

**Config:**

```
RRF_ENABLED=true
ISF_ENABLED=true
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

| Item | Value |
|------|--------|
| Deploy | [30182313845](https://github.com/Cobra4152021/cobra-core/actions/runs/30182313845) suffix `kc026g` |
| Offline harness | 7/7 PASS |
| Health `rrfGate` | `rrfEnabled=true`, `liveGateOpen=false`, `activeProfile=default` |
| Catalog | `["mock"]` only |
