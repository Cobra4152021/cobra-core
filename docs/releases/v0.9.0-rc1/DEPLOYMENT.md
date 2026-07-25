# Deployment — Cobra Core v0.9.0-rc1

## Intended topology

```
Operator host (loopback)
  └─ cobra-protocol-v1  (127.0.0.1:PORT)
        ↑ Bearer only
  └─ Optional: named tunnel / Worker (Computer staging) — separately authorized
```

RC1 server **refuses non-loopback binds**.

## Steps

1. Install `0.9.0rc1` wheel or editable package.
2. Export configuration (see CONFIGURATION.md).
3. Start: `cobra-protocol-v1`
4. Verify: `GET /health` with Bearer → ready/identity fields.
5. Verify: `POST /v1/chat/completions` with `stream:false`.
6. Optional: `GET /metrics` with Bearer.

## Restart

Stop process (SIGINT/SIGTERM) → start again with same env.  
Admission daily counters reset on process restart (process-local).

## Upgrade

1. Stop server.
2. Install new wheel.
3. Confirm Protocol/compat still `1`/`1`.
4. Start and re-run health + one completion.

## Shutdown

- Graceful: SIGINT/SIGTERM triggers `httpd.shutdown`
- Kill switch without stop: `COBRA_CORE_ENABLED=false` and restart, or rely on process stop
