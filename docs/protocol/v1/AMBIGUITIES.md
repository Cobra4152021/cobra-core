# Protocol V1 — ambiguities and narrow server choices

Frozen client contract: `ENDPOINT_CONTRACT.md` (Cobra Computer).  
Where the contract is silent or underspecified for the **server**, Cobra Core chooses the **narrowest compatible** behavior.

| Topic | Ambiguity | Server choice |
| --- | --- | --- |
| Health body shape | Client only *requires* optional `revision` / `model`; King Cobra Core mission requires richer metadata | Return full health object including `protocolVersion`, `compatibilityVersion`, `providerId`, `gitSha`, `capabilities`, `limits`, `reason`, `requestId`, `latency`. Extra fields are ignored by the client parser. |
| `stream: true` | Client never sends `true` in V1; contract forbids native SSE | Accept body; **ignore** `stream` and always return one-shot JSON completion (no SSE). Documented in `STREAMING.md`. |
| Missing `x-request-id` | Client always sends on completion; health may omit | Generate `cc_<uuid>` if absent; always echo in response header and body/`requestId`. |
| Error HTTP mapping | Client maps 401/403→`auth_failed`, 400→`bad_request`, 408/504→`timeout` | Emit those statuses with JSON `{code,message,retryable,requestId}`; `retryable` always `false`. |
| Token accounting | No tokenizer mandated | Approximate `ceil(chars/4)` for prompt/completion usage. |
| Context enforcement | Client may truncate; server also responsible | Enforce `COBRA_CORE_MAX_CONTEXT` by dropping oldest turns (keep newest), ~4 chars/token. |
| Inference backend | Not specified for Phase 5B.1-CORE | Default `COBRA_INFERENCE_MODE=mock` (deterministic, no GPU). Real model load is out of scope for this phase. |
| `enabled` on health | Client flag vs server process | Running server reports `enabled: true`. Auth failure → HTTP 401 (client sets `authenticated: false`). |
| Secrets | Client uses `COBRA_CORE_AUTH_SECRET` | Server requires the same env var name for Bearer validation. |

No Protocol Version 2 behaviors are introduced.
