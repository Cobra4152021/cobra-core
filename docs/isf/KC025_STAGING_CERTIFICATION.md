# KC-025 — ISF Staging Certification

**Certification tag:** `kc-025-isf-staging-cert`  
**Branch:** `kc-025-isf-staging-cert`  
**Base commit:** `dde59ec`  
**Certification commit:** see git tag (includes adapter + harness fix)  
**Prior tags:** not modified (`kc-023-air-staging-cert`, etc.)  
**Production:** remains disabled  

## Verdict

**PASS — ISF certified end-to-end in staging**

## Workflow runs

| Phase | Config | Run ID | Container |
|-------|--------|--------|-----------|
| 5 Offline | AIR=true, ISF=true, profile=default, live=false | [30180271246](https://github.com/Cobra4152021/cobra-core/actions/runs/30180271246) | `kc025a` |
| 6 Live | AIR=true, ISF=true, profile=research, live=true | [30180340868](https://github.com/Cobra4152021/cobra-core/actions/runs/30180340868) | `kc025b` |
| 11 Live close | live=false, ISF=true, default | [30180466719](https://github.com/Cobra4152021/cobra-core/actions/runs/30180466719) | `kc025c` |
| 12 Rollback | ISF=false, AIR=true, live=false | [30180522421](https://github.com/Cobra4152021/cobra-core/actions/runs/30180522421) | `kc025d` |
| Restore | ISF=true, AIR=true, default, live=false | [30180591011](https://github.com/Cobra4152021/cobra-core/actions/runs/30180591011) | `kc025e` |

## Image

| Field | Value |
|-------|-------|
| Image tag | `v0.9.0-rc1-f41c9aca7ba7` |
| Image digest | `sha256:583a70dfc09e16e294211a9b538da09e70daf2d7f2386c9dce1d6d28fd9a5251` |
| Edge build | `kc025-edge-20260725a` |
| Staging URL | `https://cobra-core-staging.cobra4152020.workers.dev` |

## Phase results

| Phase | Result |
|-------|--------|
| 5 Offline (A–E + reject provider + metrics) | PASS (9/9) |
| 6 Live (5 skills → openai → pending_approval) | PASS (6/6) |
| 7 Governance (`kc018:approval`) | PASS (13/13) live + rollback |
| 8 Audit fields | PASS (soak audit_ok = N) |
| 9 Telemetry `/isf/metrics` | PASS |
| 10 Soak 10 / 25 / 50 | PASS (0 unexpected) |
| 11 Live gate close | PASS (3/3) |
| 12 Rollback + restore | PASS |

## Skill execution matrix (live)

| Skill | Provider | Model | Proposal |
|-------|----------|-------|----------|
| vehicle_damage_assessment | openai | gpt-5.4-mini | pending_approval |
| policy_compliance_review | openai | gpt-5.4-mini | pending_approval |
| document_comparison | openai | gpt-5.4-mini | pending_approval |
| timeline_construction | openai | gpt-5.4-mini | pending_approval |
| evidence_summary | openai | gpt-5.4-mini | pending_approval |

## Local tests

See commit notes / CI local run: full pytest green; ISF ~87% coverage.

## Known limitations

- Computer→ISF is via additive `/isf/execute` (not embedded in chat/completions body).
- Live structured results depend on provider returning schema JSON (repair allowed once).
- Offline vision skills fail closed when catalog lacks vision (by design).
- No production enablement.

## Production recommendation

**Do not enable ISF or live providers in production.** Keep staging: `ISF_ENABLED=true`, `AIR_ENABLED=true`, `CIAL_PROFILE=default`, `CIAL_LIVE_PROVIDER_ENABLED=false`.
