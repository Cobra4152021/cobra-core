# API Reference — RC1 (`/api/v1`)

Machine-readable: `GET /api/v1/openapi.json` (Bearer).

## Resource groups

| Group | Paths |
|-------|-------|
| Health | `GET /health` (public) |
| Status | `GET /status` |
| Organizations | `GET /organizations`, `GET /organizations/{id}` |
| Cases | `GET/POST /cases`, `GET /cases/{id}` |
| Workflows | `GET /workflows`, `POST /workflows/{id}/run` |
| Evidence | `GET /evidence`, `GET /evidence/{id}` |
| Plugins | `GET /plugins` |
| Benchmark | `GET /benchmark/datasets` |
| Operations | `GET /operations/status` |
| Security | `GET /security/status` |
| Reports | `GET /reports/{id}` |

Auth: Bearer (ISPF). Optional: `X-Cobra-Org-Id`, `X-Cobra-Principal-Id`, `X-Cobra-Sdk-Version`.

Errors: `error_code`, `message`, `request_id`, `timestamp`, `documentation_url`.  
Pagination: `limit`, `cursor`, `next_cursor`.  
Rate limits: `X-RateLimit-*` headers.
