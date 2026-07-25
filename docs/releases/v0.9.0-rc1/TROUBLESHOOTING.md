# Troubleshooting — Cobra Core v0.9.0-rc1

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Server won't start: auth secret required | Missing `COBRA_CORE_AUTH_SECRET` | Set secret |
| Server won't start: host must be loopback | Non-loopback bind | Use `127.0.0.1` |
| 401 on all routes | Bad/missing Bearer | Fix `Authorization: Bearer …` |
| 503 `provider_disabled` | Kill switch | Set `COBRA_CORE_ENABLED=true` if intentional |
| 429 `rate_limited` | Concurrency or daily quota | Wait / raise limits / restart process (resets day counter) |
| 504 `timeout` | Slow inference / low timeout | Raise `COBRA_CORE_TIMEOUT_MS` or reduce load |
| 503 `model_unavailable` | Local mode load failure | Check model artifacts; use `mock` for software tests |
| `/metrics` 404 | Metrics disabled | `COBRA_CORE_METRICS_ENABLED=true` |
| Governance hash mismatch | Schema/fixture edit | Revert protocol/v1 changes |

Logs must never contain prompts, responses, secrets, cookies, or JWTs.
