# Cobra Core — Endpoint Contract (Protocol Version 1)

**Authority:** Phase 5A adapter `worker/cobra/cobra-core/adapter.ts`  
**Protocol Version:** `1` (frozen Phase 5B.1)  
**Compatibility Version:** `1`  
**Do not redesign.** Future changes require Protocol Version increment + migration notes.

Constants: `COBRA_CORE_PROTOCOL_VERSION`, `COBRA_CORE_COMPATIBILITY_VERSION` in `worker/cobra/cobra-core/flags.ts`.

---

## Base URL

`COBRA_CORE_BASE_URL` — absolute HTTPS origin, no trailing slash (adapter strips trailing `/`).

Paths below are appended to that origin.

---

## Authentication

| Item | Value |
|------|--------|
| Header | `Authorization: Bearer <COBRA_CORE_AUTH_SECRET>` |
| Content-Type | `application/json` |
| Accept | `application/json` |
| Secret storage | Wrangler Secret only — never vars, never frontend, never committed |

---

## Request ID

| Item | Value |
|------|--------|
| Generation | Client (`cc_` + UUID) via `newRequestId()` |
| Propagation | Header `x-request-id` on completion requests |
| Health | Generated locally; returned in health object when enabled |
| Errors | Always include `requestId` on normalized errors |

---

## 1. Health

| Field | Contract |
|-------|----------|
| Method | `GET` |
| Path | `{BASE_URL}/health` |
| Auth | Bearer required when enabled |
| Timeout | `min(COBRA_CORE_TIMEOUT_MS, 15000)` |
| Success | HTTP 2xx; optional JSON `{ revision?: string; model?: string }` |
| Client behavior | If JSON has `revision`, health result uses remote revision |

### Disabled client response (zero network)

```json
{
  "provider": "cobra-core",
  "enabled": false,
  "reachable": false,
  "authenticated": false,
  "revision": "",
  "model": "",
  "reason": "provider_disabled",
  "latency": { "queue_ms": 0, "provider_latency_ms": 0, "inference_ms": 0, "total_ms": 0 }
}
```

### Enabled failure reasons (no or failed network)

`missing_base_url` | `missing_auth_secret` | `http_<status>` | `timeout` | `unreachable` | `ok`

---

## 2. Completion (non-streaming)

| Field | Contract |
|-------|----------|
| Method | `POST` |
| Path | `{BASE_URL}/v1/chat/completions` |
| Auth | Bearer + `x-request-id` |
| Body | See below |
| Timeout | `COBRA_CORE_TIMEOUT_MS` (default 120000) via `AbortController` |
| Cancellation | Caller `AbortSignal` aborts the same controller |

### Request body (exact adapter fields)

```json
{
  "model": "<COBRA_CORE_MODEL or override>",
  "stream": false,
  "max_tokens": <number>,
  "messages": [
    { "role": "system|user|assistant", "content": "<string>" }
  ]
}
```

| Field | Notes |
|-------|--------|
| `model` | From `COBRA_CORE_MODEL` / override; default `cobra-core-qwen3-8b` |
| `stream` | Always `false` on this path |
| `max_tokens` | Requested or 2048; capped by `COBRA_CORE_MAX_OUTPUT_TOKENS` when set |
| `messages` | System (optional) + history; truncated by approx context cap when `COBRA_CORE_MAX_CONTEXT` set (~4 chars/token) |

### Success response (parsed)

```json
{
  "choices": [{ "message": { "content": "<text>" } }],
  "usage": {
    "prompt_tokens": 0,
    "completion_tokens": 0,
    "total_tokens": 0
  }
}
```

Empty `choices[0].message.content` → normalized error `empty_response`.  
Non-JSON body → `malformed_response`.

---

## 3. Streaming (Protocol Version 1 — Computer-side behavior)

**Implemented client behavior (do not invent alternate formats):**

`streamCobraCore` does **not** open an SSE/native stream HTTP path.  
It calls `completeCobraCore` (same `POST /v1/chat/completions` with `stream: false`), then yields:

1. `{ type: "delta", text, requestId }`
2. `{ type: "done", text, requestId }`

or `{ type: "error", requestId, error }`.

### Protocol V1 implication for Cobra Core server

A Protocol Version 1 server must implement **health + non-streaming chat completions**.  
Dedicated SSE/`stream: true` is **out of Protocol Version 1** (would require Protocol Version 2).

### Documented inconsistency (Phase 5B blocker note — not silently fixed)

Adapter comment mentions “Prefer native stream endpoint”; runtime uses one-shot only.  
**Classification:** Protocol V1 frozen as one-shot-backed stream. Native stream = future protocol bump.  
**No adapter redesign in Phase 5B.1.**

---

## 4. Latency schema (normalized)

```json
{
  "queue_ms": 0,
  "provider_latency_ms": 0,
  "inference_ms": 0,
  "total_ms": 0
}
```

Disabled → all zeros.  
Completion success → `provider_latency_ms` and `inference_ms` ≈ wall clock; `queue_ms` = 0.

---

## 5. Usage schema (per-completion + snapshot)

Per response:

```json
{
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0
}
```

Adapter snapshot (`ProviderUsage`):

```json
{
  "prompt_tokens": 0,
  "completion_tokens": 0,
  "total_tokens": 0,
  "requests": 0,
  "timeouts": 0,
  "errors": 0,
  "cancelled": 0,
  "average_latency": 0
}
```

Disabled snapshot → zero.

---

## 6. Error schema (normalized)

```json
{
  "code": "<string>",
  "message": "<string>",
  "retryable": false,
  "requestId": "cc_..."
}
```

| HTTP / condition | `code` |
|------------------|--------|
| Disabled | `provider_disabled` |
| Missing URL / secret | `missing_base_url` / `missing_auth_secret` |
| 401 / 403 | `auth_failed` |
| 408 / 504 | `timeout` |
| 400 | `bad_request` |
| Other HTTP | `provider_error` |
| Abort by caller | `cancelled` |
| Abort by timer | `timeout` |
| Bad JSON | `malformed_response` |
| Empty text | `empty_response` |

**`retryable` is always `false` in Protocol Version 1.**  
**No cross-provider fallback.**

---

## 7. Context / output enforcement

| Control | Env | Behavior |
|---------|-----|----------|
| Max context | `COBRA_CORE_MAX_CONTEXT` | Approx token cap; drops oldest turns (keeps newest) |
| Max output | `COBRA_CORE_MAX_OUTPUT_TOKENS` | Caps `max_tokens` sent to server |
| Empty = unset | — | No client-side cap for that dimension |

Server-side enforcement remains Cobra Core’s responsibility; client enforces configured caps when set.

---

## 8. Revision / compatibility

| Field | Source |
|-------|--------|
| `COBRA_CORE_REVISION` | Staging/production var |
| Metadata `revision` / `gitSha` | Config revision when enabled; empty when disabled |
| Health `revision` | Remote `/health` JSON overrides when present |
| `compatibilityVersion` | Always `"1"` |

---

## 9. Shadow mode (not a public endpoint)

`shadowCobraCoreIfEnabled` requires **both** `COBRA_CORE_ENABLED=true` and `COBRA_CORE_SHADOW_MODE=true`.  
Uses the same completion path with `maxTokens: 64`. Disabled → zero network; shadow ignored.

---

## Protocol freeze

| Version | Status |
|---------|--------|
| Protocol Version 1 | **Frozen** |
| Compatibility Version 1 | **Frozen** |
| Protocol Version 2 | **Not introduced** |

Changes that alter paths, auth, body fields, or stream semantics require a new protocol version, migration notes, and compatibility documentation.
