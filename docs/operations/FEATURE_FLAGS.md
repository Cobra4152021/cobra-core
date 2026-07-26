# Feature Flags

Central registry: `FEATURE_FLAGS` (`cobra_core.operations.feature_flags`).

## Built-in flags

| Flag | Default | Purpose |
|------|---------|---------|
| `CASES_ENABLED` | false | Case management plane |
| `WORKFLOWS_ENABLED` | false | Workflow engine |
| `KEF_ENABLED` | env/`true` | Evidence gateway |
| `BENCHMARK_ENABLED` | env/`true` | Investigation benchmarks |
| `LIVE_PROVIDER_ENABLED` | env live flag | Live provider visibility |
| `READ_ONLY_MODE` | false | Deny writes |
| `ISF_ENABLED` | env/`true` | Investigation skills |
| `AIR_ENABLED` | env/`true` | Adaptive router |
| `RRF_ENABLED` | env/`true` | Resilience framework |
| `OCP_ENABLED` | true | Operations plane |

## Versioning & audit

Each change increments `version`, records `updated_by` / `updated_at`, and writes an operations audit event `feature_flag_change`. No secrets are stored in flag payloads.
