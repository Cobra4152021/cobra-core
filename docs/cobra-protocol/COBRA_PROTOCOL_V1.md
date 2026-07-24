# Cobra Protocol V1

**Protocol Version:** `1`  
**Compatibility Version:** `1`  
**Schema Version:** `1.0.0`  
**Status:** Frozen  
**Authority:** Cobra Computer adapter contract (`docs/protocol/v1/ENDPOINT_CONTRACT.md`)

This document is the Core-side normative summary of Protocol V1. It does **not** redesign the protocol. Where Computer and Core documentation diverge, the imported Computer contract wins; Core ambiguities are recorded in `docs/protocol/v1/AMBIGUITIES.md`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Provider health + identity metadata |
| `POST` | `/v1/chat/completions` | Non-streaming chat completion |

No other public endpoints are part of Protocol V1.

## Authentication

```http
Authorization: Bearer <COBRA_CORE_AUTH_SECRET>
Content-Type: application/json
Accept: application/json
```

Secret is environment/secret-store only. Never commit, log, or echo secrets.

## Request ID

| Rule | Value |
| --- | --- |
| Header | `x-request-id` |
| Client form | `cc_` + UUID (Computer) |
| Server | Honor incoming; generate `cc_` + UUID if absent |
| Errors / success | Always return `requestId` |

## Identity (metadata)

Every rich metadata response SHOULD include:

| Field | Type | Notes |
| --- | --- | --- |
| `protocolVersion` | string | `"1"` |
| `compatibilityVersion` | string | `"1"` |
| `providerId` | string | `"cobra-core"` |
| `model` | string | Configured model id |
| `revision` | string | Deployment/revision label |
| `gitSha` | string | Build/source identity |
| `capabilities` | object | Machine-readable booleans |

Computer’s minimum health parse accepts optional `revision` / `model`. Extra identity fields are compatible and required by Core Phase 5B.1 server policy.

## Capabilities

Machine-readable keys (extensible without protocol redesign when new keys are additive and default-safe):

| Key | Protocol V1 meaning |
| --- | --- |
| `streaming` | Computer-compatible one-shot-backed streaming (not native SSE) |
| `vision` | Multimodal image inputs |
| `toolCalling` | Tool / function calling |
| `jsonMode` | Structured JSON mode |
| `thinking` | Explicit thinking / reasoning channel |
| `embeddings` | Embeddings endpoint family |

Unknown capability keys MUST be ignored by clients. Removing or redefining a key’s meaning requires a Compatibility or Protocol review.

## Health

`GET /health` MUST NOT execute inference.

Normalized success fields include provider enablement, auth/reachability, protocol/compat versions, revision/gitSha, capabilities, limits, reason, latency, and requestId. See `protocol/v1/schemas/health.response.schema.json`.

## Completion

`POST /v1/chat/completions` with `stream: false` (Protocol V1 wire path).

Request body fields (Computer-frozen):

```json
{
  "model": "string",
  "stream": false,
  "max_tokens": 2048,
  "messages": [
    { "role": "system|user|assistant", "content": "string" }
  ]
}
```

Success MUST include `choices[0].message.content` and normalized `usage`. Core also returns `latency`, protocol/compat versions, and `requestId` (additive, compatible).

## Streaming (V1)

Protocol V1 does **not** define native SSE. Computer `streamCobraCore` calls the same non-streaming completion, then yields local `{type:"delta"|"done"|"error"}` events. See fixture `streaming.json` and `docs/protocol/v1/STREAMING.md`.

## Limits

| Limit | Semantics |
| --- | --- |
| Context | Approx token cap (~4 chars/token); drop oldest turns |
| Output | Cap `max_tokens` |
| Timeout | Return normalized `timeout` |

## Usage

```json
{
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0
}
```

## Latency

Monotonic timing preferred:

```json
{
  "queue_ms": 0,
  "provider_latency_ms": 0,
  "inference_ms": 0,
  "total_ms": 0
}
```

## Errors

Normalized shape only — see `ERROR_CODES.md`. Never expose tracebacks, filesystem paths, environment contents, or container internals.
