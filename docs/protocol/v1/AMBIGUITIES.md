# Protocol V1 — ambiguities and narrow server choices

Frozen client contract: `ENDPOINT_CONTRACT.md` (Cobra Computer).  
Where the contract is silent or underspecified for the **server**, Cobra Core chooses the **narrowest compatible** behavior.

| Topic | Ambiguity | Server choice |
| --- | --- | --- |
| Health body shape | Client only *requires* optional `revision` / `model`; King Cobra Core mission requires richer metadata | Return full health object including `protocolVersion`, `compatibilityVersion`, `providerId`, `gitSha`, `capabilities`, `limits`, `reason`, `requestId`, `latency`. Extra fields are ignored by the client parser. |
| `stream: true` | Client never sends `true` in V1; governance `completion.request.schema.json` requires `stream: false` | **Reject** non-false `stream` with `bad_request` (schema wins over older ignore-and-continue choice). Streaming compatibility remains one-shot-backed after a valid `stream:false` completion. |
| Missing `x-request-id` | Client always sends on completion; health may omit | Generate `cc_<uuid>` if absent; always echo in response header and body/`requestId`. |
| Error HTTP mapping | Client maps 401/403→`auth_failed`, 400→`bad_request`, 408/504→`timeout` | Emit those statuses with JSON `{code,message,retryable,requestId}`; `retryable` always `false`. |
| Token accounting | No tokenizer mandated | Mock: `ceil(chars/4)`. Local: tokenizer counts when available. See `TOKEN_COUNTING.md`. |
| Context enforcement | Client may truncate; server also responsible | Truncate oldest turns (fixture). If newest alone exceeds cap → `context_limit` error (schema-allowed code string). |
| Output enforcement | Cap vs reject | Cap `max_tokens` to `COBRA_CORE_MAX_OUTPUT_TOKENS` (fixture). |
| Latency on errors | Phase asks for latency on errors; `error.schema.json` has `additionalProperties:false` | **Do not** attach latency to error bodies (governance schema wins). |
| Inference backend | Optional real runtime | Default `mock`. Optional `local`/`qwen-local` uses existing Qwen3-8B NF4 adapter; not required for conformance. |
| `enabled` on health | Client flag vs server process | Running server reports `enabled: true`. Auth failure → HTTP 401 (client sets `authenticated: false`). |
| Secrets | Client uses `COBRA_CORE_AUTH_SECRET` | Server requires the same env var name for Bearer validation. |

No Protocol Version 2 behaviors are introduced.
