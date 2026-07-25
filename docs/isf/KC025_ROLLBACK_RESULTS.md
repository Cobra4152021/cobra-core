# KC-025 — Rollback Results

## Rollback config

```
ISF_ENABLED=false
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

Expected:

- `/isf/execute` → `isf_disabled` (503)
- Legacy `/v1/chat/completions` mock path remains
- AIR remains enabled
- pending_approval / Computer approval suite remains green

## Restore after certification

```
ISF_ENABLED=true
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

_Staging run results to be filled after Phase 12 deploy._
