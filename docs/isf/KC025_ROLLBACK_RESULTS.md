# KC-025 — Rollback Results

## Rollback config (run 30180522421, container `kc025d`)

```
ISF_ENABLED=false
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

| Check | Result |
|-------|--------|
| `isfGate.isfEnabled` | false |
| `airGate.airEnabled` | true |
| `/isf/execute` | 503 `isf_disabled` |
| Legacy `/v1/chat/completions` mock | 200 |
| Computer `kc018:approval` | 13/13 PASS |

## Restore after certification (run 30180591011, container `kc025e`)

```
ISF_ENABLED=true
AIR_ENABLED=true
CIAL_PROFILE=default
CIAL_LIVE_PROVIDER_ENABLED=false
```

Offline cert re-run: **9/9 PASS**.
