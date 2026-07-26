# Quotas

Daily UTC counters with three thresholds:

| Tier | Default relative to hard |
|------|---------------------------|
| warning | 75% |
| soft_limit | 90% |
| hard_limit | 100% |

## Tracked counters

- `cases_per_day`
- `workflow_executions_per_day`
- `provider_calls_per_day`
- `vault_retrievals_per_day`
- `benchmark_runs_per_day`

## Enforcement model

- `allow(name)` — True if hard limit would not be exceeded
- `consume(name)` — increments usage; hard exceed audits + metrics
- Soft/warning are informational for operators/alerts
- Hard limit `0` means unlimited (tracking still available)

Quota changes are audited (`quota_change`).
