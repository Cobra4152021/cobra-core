# KC-021 — Staging Deployment Results

## Status

**PASS** — Phases 1–6 completed on staging. Live OpenAI-compatible provider
certified for staging only. Production remains disabled. No merge.

Certification tag: `kc-021-live-provider-staging-cert` (created after this record).

## Final rollback deploy (Phase 6)

| Field | Value |
|-------|-------|
| Branch | `kc-021-live-provider-cert` |
| Deployed commit | `06be494` |
| Workflow | [30176022544](https://github.com/Cobra4152021/cobra-core/actions/runs/30176022544) |
| Image tag | `v0.9.0-rc1-06be494e613e` |
| Image digest | `sha256:14249cd78265d27f28acfd3819a1e9da5116509308acac413fd22187444c1d2f` |
| Worker version ID | `fdb92c04-110d-45b1-8cef-569e5502cf5f` |
| APP_ENV | staging |
| Profile | `default` |
| Live flag | `false` |
| canUseLive | `false` |

## Phase summary

| Phase | Status | Evidence |
|-------|--------|----------|
| 1 Mock-safe deploy | PASS | Prior record; mock proposal `pending_approval` |
| 2 Provider configured, gate closed | PASS | Secret bound; vars set; mock only ([301](https://github.com/Cobra4152021/cobra-core/actions/runs/30174324646)) |
| 3 Research + live activation | PASS | `canUseLive=true`; live completion `pong` (non-mock) |
| 4 E2E + approval/reject | PASS | Live proposal HTTP 201; `kc018:approval` 13/13 |
| 5 Soak 10/25/50 | PASS | 100% success each stage (see soak doc) |
| 6 Rollback to mock | PASS | Mock completion + mock proposal `pending_approval` |

## Phase 2 — Configure live provider, gate closed

| Check | Result |
|-------|--------|
| `OPENAI_API_KEY` bound (GHA secret → Worker secret) | PASS (value not logged) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` |
| `OPENAI_MODEL` | `gpt-5.4-mini` |
| `CIAL_PROFILE=default` / live flag `false` | PASS |
| Completion mock prefix | PASS `[mock]…` |
| Live model identity absent | PASS |
| Computer proposal `pending_approval` | PASS |

## Phase 3 — Research activation

| Check | Result |
|-------|--------|
| `CIAL_PROFILE=research` + live flag `true` | PASS |
| Worker `/cial-gate` openaiKeyConfigured | PASS |
| Container `cialGate.canUseLive` | PASS |
| Live minimal inference (non-mock) | PASS |
| Direct OpenAI probe (`max_completion_tokens`) | PASS HTTP 200 |
| Certified revision pin | PASS `ec400d83…` |
| Production not enabled | PASS `APP_ENV=staging` |

Fixes required for live path (recorded for ops):

1. Secrets before container boot (workflow order).
2. Unique image tags per commit (stale `:v0.9.0-rc1` digest).
3. GPT-5 `max_completion_tokens` (not `max_tokens`).
4. `CIAL_LIVE_MAX_OUTPUT_TOKENS=2048` for Computer proposals (was 256).

## Phase 4 — Computer E2E + approval regression

| Check | Result |
|-------|--------|
| Live proposal create | PASS HTTP 201 `pending_approval` (non-mock draft) |
| Approve + audit | PASS |
| Reject + audit | PASS |
| Cancel unsupported / duplicate / unauthorized | PASS |
| `npm run kc018:approval` | PASS 13/13 |

## Phase 5 — Soak

See `KC021_SOAK_RESULTS.md`. All stages 100% success; no mock regression;
no auth leakage; revision pin held.

## Phase 6 — Rollback

| Check | Result |
|-------|--------|
| Profile `default` / live `false` | PASS |
| `canUseLive=false` | PASS |
| Core mock completion | PASS |
| Computer mock proposal `pending_approval` | PASS |
| Production still disabled | PASS |

## Security findings

- No credentials committed or logged.
- OpenAI probe logs only HTTP status + error code/type/param.
- Health `cialGate` exposes booleans/hosts/profile only (no keys/prompts).
- Invalid-key staging mutation not performed (would leave staging broken);
  taxonomy covered by simulated harness `auth_401`; positive live auth proven
  by successful inference.

## Estimated cost (staging live window)

Controlled soak + E2E only. Soft ceiling `CIAL_LIVE_DAILY_COST_CEILING=5.00`.
No abnormal cost growth observed during soak (small `max_tokens=16` stages).

## Remaining (out of scope)

- Production enablement — **refused**
- Automatic merge — **not performed**
- Multi-provider fallback — not in scope
