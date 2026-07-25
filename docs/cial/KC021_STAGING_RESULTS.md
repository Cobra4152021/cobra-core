# KC-021 — Staging Deployment Results

## Status

**PARTIAL** — Phase 1 (mock-safe deploy) completed. Phases 2–6 blocked pending
operator-supplied live provider secrets/config.

Production remains disabled.

## Deploy metadata

| Field | Value |
|-------|-------|
| Branch | `kc-021-live-provider-cert` |
| Deployed commit | `f46e324` |
| Workflow | [30171261323](https://github.com/Cobra4152021/cobra-core/actions/runs/30171261323) |
| Conclusion | success |
| Image | `registry.cloudflare.com/ef3a70f5368245d987e2f2bb4a351b4a/cobra-core-staging:v0.9.0-rc1` |
| Image digest | `sha256:e829ad250a79f06833c7a49a61f5912ea3bbc5dfcde63e7f80b9ef524d34a4b7` |
| Worker version ID | `b6fa3d64-3f7a-4017-8f86-0443c1bf81c4` |
| Deployed at (UTC) | 2026-07-25T19:16:58Z |
| APP_ENV | staging |
| Profile | `default` |
| Live flag | `false` |

## Phase 1 — Mock-safe deploy

| Check | Result |
|-------|--------|
| GHA cloud build/deploy | PASS |
| Core `/health` | PASS `healthy` |
| Version | PASS `v0.9.0-rc1` |
| Certified revision | PASS `ec400d83a9cc8105557bda2105f177cc619638b2` |
| Worker root `appEnv` | PASS `staging` (not production) |
| Kill switch | PASS `false` (Core enabled for staging) |
| Completion model identity | PASS `cobra-core-qwen3-8b` |
| Mock content prefix | PASS `[mock] …` |
| Computer proposal create | PASS HTTP 201 `pending_approval` |
| Proposal model | PASS `cobra-core-qwen3-8b` |
| Human approval still required | PASS (status pending_approval) |
| OPENAI_API_KEY bound | NO (not present in GitHub secrets; intentional for Phase 1) |

Notes:
- Proposal list API returned 403 for this login path; create→`pending_approval` is the certification evidence for Phase 1.
- Remote D1 probe from this workstation failed Cloudflare auth (local token scope); does not invalidate proposal create result.

## Phase 2 — Configure live provider, gate closed

**BLOCKED** — missing operator inputs:

1. GitHub Actions secret `OPENAI_API_KEY` on `Cobra4152021/cobra-core`
2. Non-secret vars: `OPENAI_BASE_URL`, `OPENAI_MODEL` (and optional timeout/retries)

Keep after binding: `CIAL_PROFILE=default`, `CIAL_LIVE_PROVIDER_ENABLED=false`.

## Phases 3–6

**BLOCKED** until Phase 2 completes.

| Phase | Status |
|-------|--------|
| 3 Research activation | blocked |
| 4 E2E live proposal + approval regression | blocked |
| 5 Soak 10/25/50 | blocked |
| 6 Rollback proof | blocked (Phase 1 already proves mock path; full rollback after live still required) |

## Security findings (so far)

- No credentials committed.
- Workflow logged `OPENAI_API_KEY not set` (no secret echoed).
- Health/completion responses contained no auth material.
- Production not enabled (`APP_ENV=staging` only).

## Estimated cost

$0 for Phase 1 (mock only).

## Remaining blockers

1. Provide/bind `OPENAI_API_KEY` (GitHub secret) + `OPENAI_BASE_URL` + `OPENAI_MODEL`
2. Approve Phase 2–3 var updates (gate closed, then research activation)
3. Complete live E2E, soak, rollback, then certification tag
