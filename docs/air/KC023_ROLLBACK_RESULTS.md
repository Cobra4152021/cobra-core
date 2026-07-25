# KC-023 — AIR Rollback Results

## Phase 8 configuration

| Var | Value |
|-----|-------|
| AIR_ENABLED | `false` |
| CIAL_PROFILE | `default` |
| CIAL_LIVE_PROVIDER_ENABLED | `false` |
| Workflow | [30178915565](https://github.com/Cobra4152021/cobra-core/actions/runs/30178915565) |
| Container | `staging-rc1-kc023d` |

## Verification

| Check | Result |
|-------|--------|
| `airGate.airEnabled` | `false` |
| `POST /air/route` | HTTP 503 `air_disabled` |
| `POST /v1/chat/completions` | mock `[mock]` via legacy DeterministicRouter |
| Computer `kc018:approval` | **13/13 PASS** |

## Post-cert restore

Restored operational staging to:

- `AIR_ENABLED=true`
- `CIAL_PROFILE=default`
- `CIAL_LIVE_PROVIDER_ENABLED=false`

Workflow: [30178981967](https://github.com/Cobra4152021/cobra-core/actions/runs/30178981967) (`kc023e`).

## Conclusion

Legacy routing restores cleanly. AIR-specific routes disable without breaking Protocol V1 or the human approval gate. Production remains disabled.
