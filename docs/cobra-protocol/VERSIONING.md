# Versioning & Protocol Evolution

## Version fields

| Field | Meaning | Protocol V1 value |
| --- | --- | --- |
| Protocol Version | Wire contract generation | `1` |
| Compatibility Version | Negotiation within a protocol generation | `1` |
| Schema Version | Governance JSON Schema / OpenAPI package | `1.0.0` |

Schema Version may patch (`1.0.x`) for documentation-only clarifications that do not change validation semantics. Semantic changes to schemas/fixtures require at least a Schema Version minor bump and MANIFEST hash regeneration.

## When to increment

| Change | Protocol | Compatibility | Schema |
| --- | --- | --- | --- |
| Docs typo only | — | — | patch optional |
| Additive optional response field | — | usually — | minor |
| New capability key (default false / ignorable) | — | usually — | minor |
| New required request field | major | reset/review | major |
| Path / auth / stream semantics change | major | reset | major |
| Error code meaning change | major or compat review | maybe bump | minor/major |

## Evolution process (required)

1. **Proposal** — Written change proposal: motivation, affected endpoints, breaking vs additive, Computer impact, Core impact.
2. **Compatibility review** — Decide Protocol vs Compatibility vs Schema-only bump using this document and `COMPATIBILITY_POLICY.md`.
3. **Schema update** — Edit `protocol/v1/schemas/` and `openapi.yaml`; update TypeScript types.
4. **Fixture update** — Update `protocol/v1/fixtures/` to match; no live GPU required.
5. **Computer validation** — Adapter / client conformance against fixtures and OpenAPI; Computer repo tests green.
6. **Core validation** — Core server (or mock) conformance; Core tests green; `cobra-protocol-conformance` green.
7. **Version increment** — Bump the agreed version fields; regenerate `MANIFEST.json` hashes and `sourceCommit`.
8. **Dual repository testing** — Both Computer and Core CI (or local paired runs) must pass before merge to mainlines.

## Dual repository testing checklist

- [ ] Computer adapter still parses health + completion fixtures
- [ ] Core server still serves Contract V1 (or explicit new version)
- [ ] Auth failure fixtures unchanged in meaning
- [ ] Limits / timeout / usage / latency fixtures validated
- [ ] Streaming fixture still matches one-shot-backed V1 semantics (unless Protocol ≥ 2)
- [ ] MANIFEST hashes match committed artifacts
- [ ] No secrets in fixtures or docs

## Freeze rule

Protocol Version `1` / Compatibility Version `1` remain frozen until a proposal completes the full evolution process. Do not silently “fix” the wire by inventing fields Computer does not understand as required.
