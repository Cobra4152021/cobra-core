# Rollback — Cobra Core v0.9.0-rc1

## Immediate disable (preferred)

```bash
export COBRA_CORE_ENABLED=false
# restart process OR stop process entirely
```

Expected: authenticated completions return `provider_disabled` (503).

## Full rollback

1. Stop `cobra-protocol-v1`.
2. Delete/rotate `COBRA_CORE_AUTH_SECRET`.
3. `pip install cobra-core==<previous>` or check out previous git tag.
4. Confirm no listener on the Core port.
5. If a tunnel pointed at Core, stop/restrict the tunnel.
6. Capture sanitized evidence (request IDs, codes) — never secrets/prompts.

## Verification

- `/health` either fails closed or reports non-ready when process stopped
- No new successful Core completions after disable
- Computer staging (if used) should also set `COBRA_CORE_ENABLED=false`
