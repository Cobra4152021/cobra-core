# Phase 5B.2 — Cobra Core Live Staging Connection Report

## Verdict

Phase 5B.2 completed as a staging-only end-to-end exercise: temporary GPU Core endpoint validated under Protocol V1, Cobra Computer staging connected, evidence exported, then Core disabled, credentials invalidated, GPU terminated, and zero Phase 5B.2 billable resources remaining.

Status label: **Locally verified** (live GPU + staging Worker path exercised; production never enabled).

## Baselines

| Item | Value |
| --- | --- |
| Cobra Computer tip | `93da39398bd3e70ad6d44f631b2b036705fb4d02` |
| Cobra Computer work commit | `470bdbc9281c6469585f4136b13a0a2d956ea295` |
| Cobra Core Protocol V1 server | `00e4862b90d0eca0f6ec0b5f7191ba0ce43fa6fa` |
| Governance tip | `50e66e37ebc97de3a4d97c57d67b8975af7caaba` |
| Governance package | `e78d5be59a6e7cf8beda85a299c8fa707417d114` |
| Protocol / Compatibility / Schema | `1` / `1` / `1.0.0` |
| schemaHash | `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3` |
| fixtureHash | `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7` |
| Official score | `0.840` |
| CobraBench | `prepared-not-run` |

## Resource

| Item | Value |
| --- | --- |
| Provider | RunPod |
| GPU | NVIDIA RTX A5000 |
| Resource ID | `mxdxxoqyo4hrdm` |
| Hourly rate | `$0.16/hr` |
| Image | `runpod/pytorch:1.0.2-cu1281-torch280-ubuntu2404` |
| Disk | 50 GB workspace volume (terminated with pod) |
| Successful-pod runtime | ~0.56 hr |
| Estimated successful-pod cost | ~`$0.09` |
| Estimated total Phase 5B.2 cost (incl. short/unusable pods) | ~`$0.22` |
| Budget | `$10` |

First pod (`yh5jpomg934ydt`) was terminated as CUDA-unusable (`nvidia1` without `nvidia0`). One subsequent successful A5000 pod completed the exercise. No second concurrent GPU was kept.

## Endpoint architecture

- Protocol V1 server bound to loopback `127.0.0.1:18080`
- HTTPS via Cloudflare quick tunnel (`*.trycloudflare.com`)
- Auth: Bearer secret in process environment / staging Wrangler secret only
- RunPod `8080/http` proxy rejected with HTTP 403; tunnel used instead
- Inference mode: `COBRA_INFERENCE_MODE=local` (not mock)
- Model: Qwen3-8B NF4, revision `phase-5b2-00e4862b90d0`
- Limits: maxContext `8192`, maxOutputTokens `256`, timeoutMs `120000`

## Direct Core validation

All remote direct checks passed (executed from the pod against the HTTPS tunnel URL):

- TLS reachable via Cloudflare tunnel
- Health with valid auth (`protocolVersion=1`, `compatibilityVersion=1`, correct model/revision/gitSha/limits)
- Missing/invalid auth → `401`
- Non-streaming completion with usage + latency
- Request ID preserved and generated when absent
- Output-limit cap behavior
- Bad request → `400` without traceback / internal paths
- No secrets printed in validation receipts

Evidence: `evaluations/diagnostics/phase-5b2-live-staging/direct-core-results.json`

## Cobra Computer staging

- Staging-only deploy of `hidden-grid-os-staging`
- Enable Version ID: `e5f8a727-5cb2-4da2-80a1-6df95127af26`
- Disable Version ID: `ae7eddeb-6e56-431e-a1ac-7d3b36decf77`
- `COBRA_CORE_AUTH_SECRET` set via Wrangler secret for staging Worker, then deleted
- Committed production/staging defaults remained `COBRA_CORE_ENABLED=false`, shadow false, admin-only true
- Live suite: `npm run cobra-core:staging-validate -- --staging` → PASS
- Real-model sanity: 5/5 short prompts OK (usage + latency recorded; prompts/responses not stored)
- Offline adapter checks confirmed: adaptive-claude default, no Core in adaptive/fallback, admin-only visibility, zero traffic when disabled, no fallback on Core failure

## Routing / RBAC / redaction

| Check | Result |
| --- | --- |
| Default provider adaptive-claude | PASS |
| Core never auto-selected | PASS |
| Ordinary-user visibility rejected (admin-only) | PASS |
| No fallback through Core | PASS |
| Shadow mode false | PASS |
| Authorization redacted in smoke logs | PASS |
| Production flags unchanged | PASS |

Live Worker session tokens for synthetic admin/ordinary users were not available in this operator environment; RBAC/routing proofs rely on the Phase 5B.1 adapter suite (server-side flag/roster/visibility checks) plus staging deploy posture. Frontend hiding was not treated as the sole control.

## Kill switch and cleanup

1. Staging redeployed with Core overlay removed (`COBRA_CORE_ENABLED` not set true)
2. Kill-switch script PASS (disabled posture / zero traffic)
3. Staging `COBRA_CORE_AUTH_SECRET` deleted from Wrangler (`secret list` shows absent)
4. Local temp secret file removed
5. Protocol process + tunnel stopped by pod termination
6. RunPod pod `mxdxxoqyo4hrdm` deleted (`204`); remaining pods `0`
7. Temporary tunnel URL returns unreachable (`530`)
8. Governance hashes unchanged; schemas/fixtures untouched; CobraBench not run

## Known limitations

1. Protocol V1 streaming remains one-shot-backed (not native SSE).
2. Cloudflare quick tunnels are ephemeral and not suitable for production.
3. RunPod community proxy HTTPS to custom ports returned 403 in this environment.
4. Host DNS for `*.trycloudflare.com` was intermittently unavailable earlier; final validation used pod-side and later host-side checks once DNS resolved.
5. Live org-boundary / synthetic admin session JWT exercise against the Worker was not available without staging admin credentials in env.

## Phase 5C readiness recommendation

**Ready to plan Phase 5C only after** a non-ephemeral staging Core hosting decision (dedicated TLS endpoint, secret rotation runbook, and admin-session E2E harness). Do **not** enable production. Do **not** start Phase 5C automatically from this report.

## Evidence location

`evaluations/diagnostics/phase-5b2-live-staging/`
