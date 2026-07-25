# KC-021 — Security Review

## Trust boundaries

- Computer ↔ Core: Protocol V1 only
- Core ↔ provider: HTTPS OpenAI-compatible API inside Core process
- Secrets: GitHub Actions / Cloudflare Worker secrets only

## Controls verified in code (pre-live)

| Control | Status |
|---------|--------|
| `CIAL_LIVE_PROVIDER_ENABLED` default false | yes |
| Production `APP_ENV` cannot activate live | yes |
| API key not in git / docs / fixtures | yes |
| `CialConfig` / provider `repr` redacts key | yes |
| Error messages omit response bodies / auth headers | yes |
| Container env passes key only via secret binding | yes (Worker env) |
| Plain wrangler vars contain no keys | yes |

## Logging policy

Allowed: provider id, model id, routing policy, route reason, latency, retry
counts, token estimates, health, error category, request/proposal ids.

Forbidden: API keys, Authorization headers, prompts, evidence, full responses,
investigative PII.

## Live auth negative test (post-deploy)

1. Temporarily bind invalid `OPENAI_API_KEY`.
2. Expect CIAL `authentication_failed` → Protocol `auth_failed` / provider error path.
3. Restore valid secret and bump container instance.
4. Confirm no key material in logs or API responses.

## Findings (pre-deploy)

No credential commits identified in KC-021 diff. Live leakage checks remain
**pending** until staging deploy with secrets.
