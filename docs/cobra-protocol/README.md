# Cobra Protocol — Governance

**Phase:** 5B.1A  
**Scope:** Documentation, schemas, fixtures, OpenAPI, TypeScript types, and drift protection.  
**Out of scope:** Server logic, inference logic, deployment, GPU, CobraBench.

## Authority

| Asset | Owner | Location |
| --- | --- | --- |
| Protocol contract (frozen) | Cobra Computer | Imported mirror: `docs/protocol/v1/` |
| Server implementation | Cobra Core | `src/cobra_core/protocol_v1/` (not modified by this phase) |
| Governance / schemas / fixtures | Cobra Core | `protocol/v1/` + this directory |

Protocol Version **1** and Compatibility Version **1** are frozen. Changes require the evolution process in `VERSIONING.md` and dual-repository validation.

## Contents

| Document | Purpose |
| --- | --- |
| [COBRA_PROTOCOL_V1.md](./COBRA_PROTOCOL_V1.md) | Normative Protocol V1 summary |
| [COMPATIBILITY_POLICY.md](./COMPATIBILITY_POLICY.md) | Compatibility Version rules |
| [VERSIONING.md](./VERSIONING.md) | Version increments + evolution process |
| [ERROR_CODES.md](./ERROR_CODES.md) | Normalized error codes |
| [SECURITY.md](./SECURITY.md) | Auth, secrets, safe errors |
| [CONFORMANCE_TESTING.md](./CONFORMANCE_TESTING.md) | Conformance command and gates |

## Machine-readable package

```text
protocol/v1/
  MANIFEST.json          # versions + content hashes
  openapi.yaml           # OpenAPI 3.1
  schemas/*.schema.json  # JSON Schema (Draft 2020-12)
  types/cobra-protocol-v1.ts
  fixtures/*.json
```

## Conformance

```bash
cobra-protocol-conformance
# or
python -m cobra_core.protocol_governance
```

Verifies schema hash, fixture hash, schema/fixture structural validity, OpenAPI presence, TypeScript types presence, and MANIFEST integrity.

## Related

- Frozen endpoint contract: `docs/protocol/v1/ENDPOINT_CONTRACT.md`
- Streaming honesty note: `docs/protocol/v1/STREAMING.md`
- Ambiguities (narrow choices): `docs/protocol/v1/AMBIGUITIES.md`
