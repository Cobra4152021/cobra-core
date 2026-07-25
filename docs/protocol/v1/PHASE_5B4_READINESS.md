# Phase 5B.4 — Readiness Remediation (Core note)

Computer-owned deliverables live in Cobra Computer
`docs/cobra-core-integration/` (blocker matrix, durable staging design,
monitoring, policy, rollback, verify waiver).

## Governance (this repo)

Ran `cobra-protocol-conformance` via `PYTHONPATH=src`:

- **PASS**
- Protocol Version `1` unchanged
- Compatibility Version `1` unchanged
- Schema Version `1.0.0` unchanged
- schemaHash `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3` unchanged
- fixtureHash `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7` unchanged

No OpenAPI / TypeScript types / fixture edits in this phase.

## Baselines

| Item | Value |
| --- | --- |
| Core tip (docs) | `0983d677c603bd3b901935c74acd39e96880dec3` |
| Protocol V1 server pin | `00e4862b90d0eca0f6ec0b5f7191ba0ce43fa6fa` |
| Official score | `0.840` |
| CobraBench | `prepared-not-run` |

## Durable staging

Design selected on Computer side: RunPod pod + named Cloudflare Tunnel.
**Not provisioned** in 5B.4.
