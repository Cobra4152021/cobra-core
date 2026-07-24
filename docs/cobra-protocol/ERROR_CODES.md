# Protocol V1 Error Codes

Normalized error object (always):

```json
{
  "code": "string",
  "message": "string",
  "retryable": false,
  "requestId": "cc_..."
}
```

**Protocol V1:** `retryable` is always `false`. No cross-provider fallback.

## Codes

| Code | Typical HTTP | Meaning |
| --- | --- | --- |
| `auth_failed` | 401 | Missing/invalid Bearer; auth not configured |
| `bad_request` | 400 | Invalid JSON shape or field values |
| `timeout` | 408 / 504 | Deadline exceeded |
| `provider_error` | 5xx / other HTTP | Generic provider failure |
| `provider_disabled` | 503 | Provider disabled (often client-local) |
| `missing_base_url` | — | Client config (Computer) |
| `missing_auth_secret` | — | Client config (Computer) |
| `malformed_response` | 502 | Non-JSON or unusable body |
| `empty_response` | 502 | Empty completion text |
| `cancelled` | 499 | Caller abort |

Computer may synthesize `http_<status>` style reasons on health failure paths; Core server responses use the normalized object above.

## Safety

Error `message` MUST be safe for clients:

- No Python/JS tracebacks
- No filesystem paths
- No environment variable names/values or secrets
- No container / host inventory details

See `SECURITY.md`.
