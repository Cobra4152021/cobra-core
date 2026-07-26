# Identity

Every request has exactly one authenticated principal.

## Principal types

| Type | Use |
|------|-----|
| `user` | Human operators |
| `service` | Internal services (Vault, Operations, Benchmark) |
| `api_client` | Machine clients |
| `plugin` | Plugin runtime identity |
| `workflow` | Workflow execution identity |
| `system` | Cobra system principal |

## Bootstrap

- `sys_cobra` — system principal with administrator role (explicit permissions only)
- `svc_evidence_vault` — retrieve_evidence (+ service baseline)
- `svc_operations` — manage_operations, view_metrics
- `svc_benchmark` — run_benchmark, view_metrics

Attributes never store passwords, API keys, or raw tokens in public views.
