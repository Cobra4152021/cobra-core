# Compatibility Policy

**Protocol Version:** `1`  
**Compatibility Version:** `1` (frozen with Protocol V1)

## Purpose

Compatibility Version lets Computer and Core negotiate safely without redesigning Protocol V1 for every additive metadata change.

## Rules

1. **Same Compatibility Version** means both sides agree on wire paths, auth, request body fields, success parse requirements, error shape, and stream semantics for that Protocol Version.
2. **Additive, ignored-if-unknown fields** (extra health keys, latency block on completion, capabilities map growth with default-false unknowns) MAY ship without a Compatibility Version bump **only if** Computer continues to function without reading them.
3. **Breaking changes** require a Protocol Version increment (preferred) or, for narrowly scoped negotiation breaks that keep paths identical, a Compatibility Version increment with dual-repo validation.
4. Clients MUST ignore unknown JSON fields.
5. Servers MUST NOT require fields that Computer does not send under Protocol V1.
6. `retryable` remains `false` for all Protocol V1 normalized errors.

## Compatibility Version `1` guarantees

| Guarantee | Status |
| --- | --- |
| `GET /health` + `POST /v1/chat/completions` | Required |
| Bearer auth | Required |
| Non-streaming completion body fields | Frozen |
| One-shot-backed Computer streaming | Frozen |
| Normalized error object | Frozen |
| Usage + latency field names | Frozen |

## Non-goals for Compatibility Version bumps alone

Do not use Compatibility Version to:

- Change URL paths
- Introduce native SSE as the only stream mode
- Change auth scheme
- Redefine `usage` or `latency` field names

Those require Protocol Version evolution (`VERSIONING.md`).

## Negotiation

Computer and Core both advertise:

- `protocolVersion: "1"`
- `compatibilityVersion: "1"`

If either side cannot satisfy Compatibility Version `1`, integration MUST fail closed (disabled / error) rather than guess.
