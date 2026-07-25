# KC-020 — OpenAI-Compatible Provider

## Status

- Continues from KC-019 CIAL foundation (`kc-019-cial`)
- Mock remains the default Internal Alpha provider
- No production enablement; no Computer changes; no Protocol V2

## Architecture

```
Protocol V1 (unchanged wire)
        |
        v
   CialEngine / DeterministicRouter
        |
        +-- mock  → MockProvider → mock_complete
        |
        +-- openai → OpenAICompatibleProvider → HTTP /chat/completions
```

The OpenAI-compatible adapter is the **reference implementation** for future
providers (Gemini, Anthropic, Cloudflare AI, etc.). All provider-specific HTTP,
retry, and schema parsing stay inside `openai_compatible.py`.

## Configuration

| Variable | Default | Notes |
|----------|---------|-------|
| `CIAL_PROVIDER` | `mock` | Alias for default provider (`mock` \| `openai`) |
| `CIAL_DEFAULT_PROVIDER` | `mock` | Used if `CIAL_PROVIDER` unset |
| `CIAL_DEFAULT_MODEL` | wire mock id / openai model | Depends on provider |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible base |
| `OPENAI_API_KEY` | unset | Required to enable live calls |
| `OPENAI_MODEL` | `gpt-4o-mini` | Provider model id |
| `OPENAI_TIMEOUT_SECONDS` | `60` | Per-request timeout |
| `OPENAI_MAX_RETRIES` | `2` | Retries for 408/429/5xx |

All optional. With no key and `CIAL_PROVIDER=mock`, behavior matches KC-018/KC-019.

## Routing

- Preferred model `cobra-core-qwen3-8b` → mock
- `CIAL_PROVIDER=openai` → internal preferred model becomes `OPENAI_MODEL`
- Manual policy validates provider/model eligibility
- **No automatic fallback** in this phase

## Health

`probe_health()` uses `GET /models`:

| Outcome | State |
|---------|-------|
| No API key | `disabled` |
| HTTP 200 | `healthy` |
| HTTP 429 / some 4xx (e.g. missing `/models`) | `degraded` |
| 401/403/5xx/connection failure/timeout | `unavailable` |

Router excludes `unavailable` and `disabled`. Degraded remains eligible.

## Security

- API keys stay in Core process environment only
- Never returned on Protocol V1, Computer APIs, logs, or audit events
- `CialConfig.__repr__` and provider `__repr__` redact secrets
- Error messages do not include response bodies or Authorization headers

## Error mapping

| Condition | CIAL code |
|-----------|-----------|
| 401 / 403 | `authentication_failed` |
| 404 | `model_not_found` |
| 408 / timeout | `timeout` |
| 429 | `rate_limited` |
| 500 / 502 / 503 / 504 | `provider_unavailable` |
| Invalid JSON / schema | `invalid_response` |
| Connection failure | `provider_unavailable` |

Mapped onward to existing Protocol V1 codes via KC-019 taxonomy.

## Supported features

- Chat completions (`stream=false`)
- JSON mode (`response_format: json_object` via request metadata)
- Timeouts + retry policy
- Structured usage tokens when provided by upstream

## Out of scope

Streaming, tools, vision, Gemini/Anthropic/Cloudflare/Ollama/OpenRouter
adapters, automatic fallback, production enablement.

## Future providers

Copy this adapter’s pattern:

1. Implement `InferenceProvider`
2. Keep HTTP/SDK inside the adapter
3. Map failures to `CialErrorCode`
4. Register models with accurate capabilities/health
5. Add injectable transport for unit tests
