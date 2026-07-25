# KC-021 — Rollback to Mock

## Goal

Disable live OpenAI-compatible inference and restore KC-018 mock behavior
without Computer code changes.

## Steps

1. Set `CIAL_LIVE_PROVIDER_ENABLED=false` (wrangler var).
2. Set `CIAL_PROFILE=default` (or `offline`).
3. Optionally clear or leave `OPENAI_*` secrets (unused when live gate closed).
4. Redeploy Worker via GitHub Actions (unique image tag per commit).
5. Bump container instance name if envVars did not reload.
6. Verify `GET /health` (Bearer) — healthy, certified revision unchanged.
7. Create a mock proposal from Computer → expect `pending_approval`.
8. Confirm audit continuity and no automatic approval.

## Expected CIAL behavior

- OpenAI provider is not registered when live gate is closed.
- If `CIAL_PROFILE=research` without the live flag, engine forces mock/offline with
  route reason `profile_live_unavailable_use_offline`.

## Verification checklist (Phase 6 executed 2026-07-25)

- [x] Core health OK
- [x] Mock proposal `pending_approval`
- [x] `canUseLive=false` / profile `default`
- [x] No Computer deploy required
- [x] Production still disabled

Rollback deploy: commit `06be494`, workflow
https://github.com/Cobra4152021/cobra-core/actions/runs/30176022544
