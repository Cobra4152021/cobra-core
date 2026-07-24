# Phase 5B.1-CORE — Protocol V1 Server Implementation Report

**Status:** Local verification complete  
**Protocol Version:** `1`  
**Compatibility Version:** `1`  
**GPU / cloud / deploy / CobraBench:** none  
**Official score:** **0.840** unchanged  

## Server architecture

- Package: `src/cobra_core/protocol_v1/`
- Transport: stdlib `ThreadingHTTPServer` (loopback-only guard)
- Inference default: `COBRA_INFERENCE_MODE=mock` (deterministic; no weights/GPU)
- Contract import: `docs/protocol/v1/ENDPOINT_CONTRACT.md` (+ freeze + ambiguities)

```text
Cobra Computer adapter  --Bearer-->  GET /health
                                    POST /v1/chat/completions (stream=false)
                                         |
                                         v
                              protocol_v1 handlers
                                         |
                                         v
                              mock inference (Phase 5B.1-CORE)
```

## Endpoints

| Method | Path | Auth |
| --- | --- | --- |
| `GET` | `/health` | Bearer required |
| `POST` | `/v1/chat/completions` | Bearer + optional `x-request-id` |

No debug, shell, or file endpoints.

## Capabilities

```json
{
  "streaming": true,
  "vision": false,
  "toolCalling": false,
  "jsonMode": false,
  "thinking": false,
  "embeddings": false
}
```

`streaming=true` means **Computer-compatible one-shot-backed streaming**, not native SSE (`STREAMING.md`).

## Authentication

- Header: `Authorization: Bearer <COBRA_CORE_AUTH_SECRET>`
- Secret from environment only
- `hmac.compare_digest` when lengths match; never logged/echoed

## Usage

Response `usage`: `prompt_tokens`, `completion_tokens`, `total_tokens` (approx `ceil(chars/4)`).

## Latency

Monotonic `perf_counter` → `queue_ms` (0), `provider_latency_ms`, `inference_ms`, `total_ms`.

## Errors

Normalized `{code,message,retryable,requestId}` with `retryable: false`.  
No tracebacks, filesystem paths, env, or container details in responses.

## Tests

- `tests/test_protocol_v1_conformance.py`
- `scripts/smoke_protocol_v1.py`

## Smoke results

Recorded at commit time via local smoke script (see verification section in final chat report).

## Known limitations

1. Mock inference only in this phase (no model load).  
2. No native SSE.  
3. Loopback bind only (`127.0.0.1` / `localhost` / `::1`).  
4. Token counts are approximate.  

## Ready for Phase 5B.2

**Yes** — Protocol V1 server surface is implemented and locally verified for Computer adapter integration once a real inference backend is attached under the same contract.
