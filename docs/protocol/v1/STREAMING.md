# Protocol V1 streaming compatibility

Cobra Computer `streamCobraCore` does **not** open SSE. It calls `POST /v1/chat/completions` with `stream: false`, then yields local `{delta}` / `{done}` events.

## Server behavior (honest)

| Item | Status |
| --- | --- |
| Native SSE / `text/event-stream` | **Not implemented** |
| `stream: true` HTTP semantics | **Not implemented** |
| One-shot JSON completion | **Implemented** (backs Computer “streaming”) |

This is Protocol Version 1 by design. Native streaming requires a future protocol version bump.
