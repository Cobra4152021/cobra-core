# Protocol Freeze — Version 1

| Field | Value |
|-------|--------|
| Protocol Version | **1** |
| Compatibility Version | **1** |
| Freeze date | Phase 5B.1 |
| Authority | `worker/cobra/cobra-core/adapter.ts` + `ENDPOINT_CONTRACT.md` |

## Constants

```ts
COBRA_CORE_PROTOCOL_VERSION = "1"
COBRA_CORE_COMPATIBILITY_VERSION = "1"
```

## Rules

1. Do **not** introduce Protocol Version 2 in this phase.
2. Any change to paths, auth, request body fields, stream semantics, or status mapping requires:
   - Protocol version increment
   - Migration notes
   - Compatibility documentation
3. Computer and Core must negotiate via Compatibility Version `1` for Protocol Version 1.

## Stream note (frozen)

Protocol Version 1 streaming on Cobra Computer is **one-shot-backed** (`POST /v1/chat/completions` with `stream: false`). Native SSE is deferred to a future protocol version.
