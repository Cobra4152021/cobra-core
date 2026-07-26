# Alerts

Informational only — no notifications, pages, or automatic remediation.

## Codes

| Code | Trigger |
|------|---------|
| `evidence_vault_unavailable` | Vault offline/degraded |
| `provider_unavailable` | CIAL degraded |
| `workflow_failures` | Workflows degraded |
| `benchmark_failures` | Benchmark degraded |
| `quota_exceeded` | Hard quota reached |
| `quota_warning` | Warning/soft tier |
| `high_latency` | Avg latency ≥ 5000ms |

All alerts set `informational_only=true`.
