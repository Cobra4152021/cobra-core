# Protocol V1 Security

## Authentication

| Rule | Requirement |
| --- | --- |
| Scheme | `Authorization: Bearer <token>` |
| Storage | Environment / secret store only |
| Logging | Never log the token or `Authorization` header value |
| Responses | Never echo the token |
| Comparison | Constant-time compare when lengths match (`hmac.compare_digest` or equivalent) |

## Surface area

Protocol V1 exposes only:

- `GET /health`
- `POST /v1/chat/completions`

Forbidden in Protocol V1 governance surface:

- Debug endpoints
- Shell / exec endpoints
- Arbitrary file read/write
- Admin reset without separate, non-Protocol channels

## Health

`/health` MUST NOT run inference and MUST NOT return secrets.

## Errors

Normalized errors only. Strip internals before responding. Prefer stable codes from `ERROR_CODES.md`.

## Fixtures & schemas

Governance fixtures MUST use fake tokens (e.g. `test-secret`, redacted `***`). Never commit real `COBRA_CORE_AUTH_SECRET` values.

## Local binding guidance

Core’s local Protocol V1 server binds loopback-only by policy. Public exposure is out of scope for Protocol V1 governance and requires a separate ops/security review (not this phase).
