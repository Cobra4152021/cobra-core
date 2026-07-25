# KC-021 — Live Provider Staging Certification

## Status

**Pre-deployment / harness complete.** Live endpoint certification, Computer E2E,
soak, and approval regression are **blocked pending explicit deploy approval**
and operator-supplied staging endpoint credentials (GitHub/Cloudflare secrets).

Production remains disabled.

## Scope

Certify the OpenAI-compatible CIAL provider against one real staging inference
endpoint, with mock rollback retained.

## Provider under test

| Field | Value |
|-------|-------|
| Provider type | OpenAI-compatible (`openai`) |
| Model ID | *operator-selected — not committed* |
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
| Simulated transport failures | local harness / pytest | implemented |
| Unit live-control tests | pytest | implemented |
| KC-018 / Protocol V1 regression | pytest | required pre-deploy |
| Live health + inference | staging after deploy | **pending approval** |
| Computer → pending_approval E2E | staging | **pending approval** |
| Approval/rejection regression | staging Computer | **pending approval** |
| Soak 10/25/50 | staging | **pending approval** |
| Rollback to mock | staging | documented; **pending execution** |

## Results placeholders (fill after live cert)

- Git commit:
- Workflow run URL:
- Container image digest:
- Worker version:
- Health result:
- Live inference summary:
- Proposal status:
- Audit result:
- Soak summary:
- Rollback result:

## Limitations

- No automatic multi-provider fallback
- No production activation
- No billing / live pricing
- Computer UI unchanged

## Remaining blockers

1. Explicit operator approval to deploy `kc-021-live-provider-cert` via GHA
2. Staging `OPENAI_BASE_URL` / model selection + `OPENAI_API_KEY` secret binding
3. Opt-in `CIAL_LIVE_PROVIDER_ENABLED=true` after safe deploy with flag false
4. Live E2E + soak + rollback evidence recording
