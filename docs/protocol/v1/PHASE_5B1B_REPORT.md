# Phase 5B.1B — Protocol V1 Server Implementation Report

**Baseline HEAD:** `50e66e37ebc97de3a4d97c57d67b8975af7caaba`  
**Governance package:** `e78d5be59a6e7cf8beda85a299c8fa707417d114`  
**Protocol / Compatibility / Schema:** `1` / `1` / `1.0.0`  
**schemaHash:** `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3` (unchanged)  
**fixtureHash:** `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7` (unchanged)

## Conflicts resolved (governance wins)

1. **`stream: true`** — frozen request schema requires `const: false`. Server **rejects** non-false `stream` (`bad_request`). Older ignore-and-continue ambiguity superseded; documented in `AMBIGUITIES.md`.
2. **Latency on errors** — Phase text asked for latency on errors; frozen `error.schema.json` has `additionalProperties: false`. Server **does not** attach latency to error bodies.
3. **Context/output errors** — fixtures define truncate/cap; unsatisfiable single-message context returns schema-allowed code `context_limit`. Output uses cap (fixture), not reject.

## Architecture

stdlib `ThreadingHTTPServer` + separated modules: config, auth, validation, request_id, inference_service, runtime_state, handlers, streaming helpers, logging_util, server lifecycle.

## Endpoints

- `GET /health`
- `POST /v1/chat/completions`

## Cancellation

Cooperative `threading.Event` for tests/hooks; broken-pipe skips late write. **No hard GPU generate cancellation.**

## Optional real model

`COBRA_INFERENCE_MODE=local|qwen-local` uses existing `QwenLocalAdapter` NF4 path. Not required for conformance; not run in this phase’s local machine smoke.
