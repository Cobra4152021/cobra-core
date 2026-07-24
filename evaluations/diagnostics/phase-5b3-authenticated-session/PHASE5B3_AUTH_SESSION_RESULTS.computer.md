# Phase 5B.3 — Authenticated Staging Session Results

## Verdict

Real staging Worker sessions proved admin-only Cobra Core access end to end. Ordinary users and cross-org probes were rejected server-side. Staging Core was disabled afterward; GPU and secret removed.

Status label: **Locally verified**

## Baselines

| Item | Value |
| --- | --- |
| Computer (includes 5B.2 evidence) | `9d003dbd3e59cc54d61749d530c817b10c14fe74` |
| Core Protocol V1 server | `00e4862b90d0eca0f6ec0b5f7191ba0ce43fa6fa` |
| Protocol / Compatibility / Schema | `1` / `1` / `1.0.0` |
| schemaHash | `f677ed325714a17ff948e3dbfaf575ec1ad3c2a3aa1940e4d05b5e49c66c32b3` |
| fixtureHash | `9cddd578ff018902f3df1069e9550de066ef54c1077ac588f2881e7c204868e7` |
| Official score | `0.840` |
| CobraBench | `prepared-not-run` |

## Test identity matrix (no credentials)

| Identity | Role | Org | Core visible | Core invoke |
| --- | --- | --- | --- | --- |
| admin_org_a | admin | A | yes | yes |
| ordinary_org_a | researcher | A | no | no (403) |
| admin_org_b | admin | B | yes (independent) | cannot use Org A chats |
| ordinary_org_b | researcher | B | no | no (403) |

## Session / JWT harness

- Mechanism: mint real `hidden_grid_session` opaque cookies into `hidden-grid-staging-db` (same pattern as KC-005/KC-012 certs)
- Target: `https://hidden-grid-os-staging.cobra4152020.workers.dev` only
- Does **not** use `HIDDEN_GRID_DEV_KEY` (maintenance bypass)
- Does **not** forge app JWTs
- Redacts cookies/Authorization in logs
- Script: `scripts/cobra-core-staging/auth-session-proof.mjs`

## Server-side gate fix (required for acceptance)

Phase 5B.2 adapter visibility existed, but Worker invoke/status did not pass session role into Core admin-only checks. This phase added:

- `handleCobraStatus(env, ctx)` filters `modelOptions` by trusted session role
- `handleCobraChat` rejects `model=cobra-core` with `403 cobra_core_forbidden` **before** quota/rate-limit/provider network when admin-only and caller is not owner/admin
- Audit action `cobra.core.denied` (no secrets/content)

## Results

| Check | Result |
| --- | --- |
| Admin session login / Worker recognition | PASS |
| Admin sees Core in `/api/cobra/status` | PASS |
| Ordinary user does not see Core | PASS |
| Admin explicit `model=cobra-core` chat | PASS (HTTP 200, Core model path, request id) |
| Ordinary direct Core invoke | PASS (`403 cobra_core_forbidden`) |
| Cross-org Org B → Org A chat | PASS (`404`) |
| Missing / malformed / expired session | PASS (`401`) |
| Tampered `active_org_id` | PASS (`404`) |
| Default selection is not Core | PASS (`adaptive-mistral` on staging runtime; committed prod default remains `adaptive-claude`) |
| Kill-switch Core absent for admin | PASS |
| Production unchanged | PASS |
| Secret deleted from staging Worker | PASS |
| GPU terminated / zero pods | PASS |

## Accounting

Authorized admin path produced Worker `requestId` (`req_…`). SSE summary did not always surface prompt token fields in the truncated stream parse; Core-side usage was previously validated in 5B.2 direct Protocol V1 tests. Rejected ordinary invokes returned before provider dispatch (no Core usage).

## Known limitations

1. Staging runtime default selection is `adaptive-mistral` (pre-existing staging env), not `adaptive-claude`. Committed production/preflight default remains `adaptive-claude`. Core is never default.
2. Cloudflare quick tunnel is ephemeral staging-only.
3. Protocol V1 streaming remains one-shot-backed.
4. Live usage token fields are best captured from Core/adapter metadata; SSE scrape may omit them.

## Phase 5C readiness

**NO** — do not enable production; do not start Phase 5C automatically. Remaining hardening for 5C planning: durable Core hosting, staging default-selection alignment if desired, and richer usage ledger export on the Worker chat path.

## Evidence

`evaluations/diagnostics/phase-5b3-authenticated-session/` (Computer + mirrored in Cobra Core repo)
