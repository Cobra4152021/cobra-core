# KC-023 — AIR Staging Certification

**Status:** Certified for staging  
**Branch:** `kc-023-air-staging-cert`  
**Certification commit:** `2b92b4194507202cd6c296e40a358be2af56cefc` (plus docs commit)  
**Base:** KC-022 `a2b466d`  
**Prior cert tag (untouched):** `kc-021-live-provider-staging-cert`  
**Suggested tag:** `kc-023-air-staging-cert`

## Deployed artifact

| Field | Value |
|-------|-------|
| Image tag | `v0.9.0-rc1-2b92b4194507` |
| Image digest | `sha256:1f0efae09b6fdc18a55a7f10e83a8ab5f7b07add426e5746f5879b370677483f` |
| Registry | `registry.cloudflare.com/ef3a70f5368245d987e2f2bb4a351b4a/cobra-core-staging` |
| Protocol pin | `ec400d83a9cc8105557bda2105f177cc619638b2` (`v0.9.0-rc1`) |
| Staging URL | `https://cobra-core-staging.cobra4152020.workers.dev` |

## Workflow run IDs

| Phase | Config | Run ID | Container suffix |
|-------|--------|--------|------------------|
| 1 Offline AIR | `AIR=true`, `CIAL_PROFILE=default`, live=`false` | [30178618993](https://github.com/Cobra4152021/cobra-core/actions/runs/30178618993) | `kc023a` |
| 2 Live AIR | `AIR=true`, `research`, live=`true` | [30178772077](https://github.com/Cobra4152021/cobra-core/actions/runs/30178772077) | `kc023b` |
| 7 Gate close | `AIR=true`, `default`, live=`false` | [30178865796](https://github.com/Cobra4152021/cobra-core/actions/runs/30178865796) | `kc023c` |
| 8 AIR rollback | `AIR=false`, `default`, live=`false` | [30178915565](https://github.com/Cobra4152021/cobra-core/actions/runs/30178915565) | `kc023d` |
| Post-cert restore | `AIR=true`, `default`, live=`false` | [30178981967](https://github.com/Cobra4152021/cobra-core/actions/runs/30178981967) | `kc023e` |

Phase 1 worker version ID: `53a9a868-b892-4548-a62d-dd57c0e09ac9`

## Configuration state (per phase)

Secrets (`COBRA_CORE_AUTH_SECRET`, `OPENAI_API_KEY`) never logged.  
`OPENAI_BASE_URL=https://api.openai.com/v1`, `OPENAI_MODEL=gpt-5.4-mini` throughout.

## Routing matrix results

| Phase | Case | Expected | Result |
|-------|------|----------|--------|
| 1 | text+offline | mock | PASS |
| 1 | reasoning+vision | `no_capability_match` | PASS |
| 1 | chat completion | mock `[mock]` | PASS |
| 1 | audit + metrics | present | PASS |
| 2 | catalog | mock+openai | PASS |
| 2 | reasoning+vision | openai / gpt-5.4-mini | PASS |
| 2 | text+offline | mock | PASS |
| 2 | research+reasoning | openai + `live_preferred` | PASS |
| 2 | unsupported capability | fail closed | PASS |
| 2 | exclude openai | fail closed | PASS |
| 3 | live completion | non-mock `pong` | PASS |
| 3 | `kc018:approval` | 13/13 | PASS |
| 7 | catalog after gate close | mock only | PASS |
| 7 | vision | fail closed | PASS |
| 8 | AIR off | route 503; legacy mock | PASS |
| 8 | approval regression | 13/13 | PASS |

## Production recommendation

**Do not enable in production.** Staging-only. Keep `CIAL_LIVE_PROVIDER_ENABLED=false` unless actively testing live AIR. Prefer `AIR_ENABLED=true` with `CIAL_PROFILE=default` for operational staging after cert.

## Known limitations

- Computer still reaches Core via Protocol V1 chat completions (profile-driven AIR); capability dry-run uses authenticated `POST /air/route`.
- Soak audit lookup completeness was 45/50 on the 50-request stage (in-memory ring; not a selection mismatch).
- Cost/latency are class labels, not live pricing.
- No additional providers beyond mock + openai.
