# Disaster Recovery

| Scenario | Procedure |
|----------|-----------|
| Cold start | Validate config → run startup validation → migrations dry-run → readiness |
| Warm restart | Liveness OK → re-run startup report → exit maintenance |
| Configuration restore | Restore backup dry-run → apply → integrity check |
| Vault unavailable | Degrade KEF/evidence paths; keep Core read/status; no object restore from Core |
| Provider unavailable | Keep routing/catalog; investigations fail closed to configured fallback |
| Partial outage | Enter maintenance; reject new workflows; preserve audit/metrics |

Always keep production enablement disabled until soak + rollback phases pass.
