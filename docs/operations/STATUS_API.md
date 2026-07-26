# Status API

Authenticated Bearer endpoints (no secrets, evidence, or case bodies):

| Method | Path |
|--------|------|
| GET | `/operations/status` |
| GET | `/operations/health` |
| GET | `/operations/usage` |
| GET | `/operations/alerts` |
| GET | `/operations/feature-flags` |
| GET | `/operations/metrics` |
| GET | `/operations/audit` |

Handlers live in `cobra_core.operations.http_api` and are mounted on Protocol V1. Staging edge proxies `/operations/*` with the same auth gate as other admin GETs.
