# Rate Limits

Limits apply per **organization** and per **API client** (fixed window).

Response headers:

- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

Defaults (overridable via env): org 600/min, client 120/min.

Exceeded requests return `429` with `error_code=rate_limited`.
