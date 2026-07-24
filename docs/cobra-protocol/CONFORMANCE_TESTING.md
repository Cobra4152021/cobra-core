# Conformance Testing

## Command

```bash
cobra-protocol-conformance
# equivalent
python -m cobra_core.protocol_governance
```

Exit code `0` = PASS. Non-zero = FAIL with reason lines on stderr/stdout.

## What it verifies

| Check | Description |
| --- | --- |
| Manifest | `protocol/v1/MANIFEST.json` present; required fields set |
| Protocol / Compatibility | Manifest versions equal `1` / `1` |
| Schema verification | All declared schema files exist; JSON Schema documents parse; required meta valid |
| Fixture verification | All declared fixtures exist; valid JSON; validate against mapped schemas |
| Protocol hash verification | Recomputed `schemaHash` and `fixtureHash` match MANIFEST |
| OpenAPI | `openapi.yaml` exists and parses |
| TypeScript types | `types/cobra-protocol-v1.ts` exists and exports expected symbols |

## Fixture map

| Fixture | Schema |
| --- | --- |
| `health.success.json` | `health.response.schema.json` |
| `completion.success.json` | `completion.response.schema.json` |
| `authentication.failure.json` | `error.schema.json` |
| `context.limit.json` | `completion.request.schema.json` (+ notes) |
| `output.limit.json` | `completion.request.schema.json` (+ notes) |
| `timeout.json` | `error.schema.json` |
| `usage.json` | `usage.schema.json` |
| `latency.json` | `latency.schema.json` |
| `streaming.json` | `streaming.events.schema.json` |

Request-limit fixtures may include a `notes` object ignored by schema validation when using envelope form — see fixture files.

## Hash algorithm

Canonical content hash (SHA-256):

1. Collect files under the category (`schemas/*.schema.json` or `fixtures/*.json`).
2. Sort by POSIX relative path.
3. For each file: update digest with `path`, NUL, raw bytes, NUL.
4. Hex-encode digest → MANIFEST field.

Regenerate MANIFEST after any schema/fixture change:

```bash
python -m cobra_core.protocol_governance --write-manifest
```

## Non-goals

- No GPU
- No live inference
- No deployment
- No CobraBench
- Does not mutate `src/cobra_core/protocol_v1/` server logic

## CI recommendation

Run `cobra-protocol-conformance` on every PR that touches `protocol/v1/` or `docs/cobra-protocol/`.
