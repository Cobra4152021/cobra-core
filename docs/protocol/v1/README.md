# Cobra Protocol Version 1 (server)

**Protocol Version:** `1`  
**Compatibility Version:** `1`  
**Authority (client):** Cobra Computer adapter — imported contract below  
**Authority (server):** this repository (`src/cobra_core/protocol_v1/`)

| Document | Role |
| --- | --- |
| [ENDPOINT_CONTRACT.md](./ENDPOINT_CONTRACT.md) | Frozen Computer↔Core endpoint contract (imported) |
| [PROTOCOL_VERSION.md](./PROTOCOL_VERSION.md) | Protocol freeze notice (imported) |
| [AMBIGUITIES.md](./AMBIGUITIES.md) | Narrowest compatible server choices |
| [STREAMING.md](./STREAMING.md) | One-shot-backed stream compatibility (no native SSE) |
| [PHASE_5B1_CORE_REPORT.md](./PHASE_5B1_CORE_REPORT.md) | Implementation report |

Do **not** redesign paths, auth, body fields, or stream semantics without a new protocol version.
