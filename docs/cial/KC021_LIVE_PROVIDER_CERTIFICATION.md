# KC-021 — Live Provider Staging Certification

## Status

**PASS — live provider certified for staging.**

Production remains disabled. Branch not merged. Certification tag:
`kc-021-live-provider-staging-cert`.

## Scope

Certify the OpenAI-compatible CIAL provider against one real staging inference
endpoint, with mock rollback retained.

## Provider under test

| Field | Value |
|-------|-------|
| Provider type | OpenAI-compatible (`openai`) |
| Model ID | `gpt-5.4-mini` |
| Base URL | `https://api.openai.com/v1` |
| Environment | staging only |
| Live flag default | `CIAL_LIVE_PROVIDER_ENABLED=false` |
| Base commit (branch start) | `9713265` (KC-020 tip on `kc-019-cial`) |

## Activation gates

Activation is **profile-centric** (`CIAL_PROFILE`). Vendors are internal.

Live research path is selected only when **all** are true:

1. `APP_ENV=staging`
2. `CIAL_ENABLED=true`
3. `CIAL_LIVE_PROVIDER_ENABLED=true`
4. `CIAL_PROFILE=research` (resolves internally to openai + `OPENAI_MODEL`)
5. `OPENAI_API_KEY` configured (secret)
6. Provider health acceptable at request time
7. `COBRA_CORE_ENABLED` / kill switch allow completions

Otherwise routing stays on **mock/offline** (`profile_live_unavailable_use_offline`).
Safe default profile: `default`.

## Safeguards

- Max input chars (`CIAL_LIVE_MAX_INPUT_CHARS`)
- Max output tokens (`CIAL_LIVE_MAX_OUTPUT_TOKENS`)
- Timeouts / retries (`OPENAI_TIMEOUT_SECONDS`, `OPENAI_MAX_RETRIES`)
- Max concurrent live requests (`CIAL_LIVE_MAX_CONCURRENT`)
- Optional daily request quota / estimated-cost ceiling
- Kill switch via existing `COBRA_CORE_KILL_SWITCH` / `COBRA_CORE_ENABLED`

Quota/cost breaches fail closed as `quota_exceeded` → Protocol `rate_limited`.

## Test matrix

| Suite | Mode | Status |
|-------|------|--------|
| Simulated transport failures | local harness / pytest | PASS |
| Unit live-control tests | pytest | PASS |
| Live health + inference | staging | PASS |
| Computer → pending_approval E2E | staging | PASS (live draft) |
| Approval/rejection regression | staging Computer | PASS 13/13 |
| Soak 10/25/50 | staging | PASS 100% |
| Rollback to mock | staging | PASS |

## Certification evidence

See `KC021_STAGING_RESULTS.md` and `KC021_SOAK_RESULTS.md`.

| Item | Value |
|------|-------|
| Final rollback commit | `06be494` |
| Rollback workflow | https://github.com/Cobra4152021/cobra-core/actions/runs/30176022544 |
| Rollback image digest | `sha256:14249cd78265d27f28acfd3819a1e9da5116509308acac413fd22187444c1d2f` |
| Worker version (rollback) | `fdb92c04-110d-45b1-8cef-569e5502cf5f` |
| Certified Core revision | `ec400d83a9cc8105557bda2105f177cc619638b2` |
| Post-cert profile | `default` / live `false` (mock restored) |

## Ops lessons (staging)

1. Bind secrets **before** container boot; bump instance after secret/var changes.
2. Tag container images per commit (`v0.9.0-rc1-<sha>`); fixed tags can pin stale digests.
3. GPT-5 family requires `max_completion_tokens` on Chat Completions.
4. Computer proposals request 2048 max tokens — set live output ceiling accordingly.

## Limitations

- No automatic multi-provider fallback
- No production activation
- No billing / live pricing
- Computer UI unchanged
- Staging invalid-key mutation not executed (positive live auth + simulated 401 taxonomy)

## Remaining blockers

None for staging certification. Production enablement remains explicitly out of scope.
