# ADR-0002 — Adaptive Intelligence Router (AIR)

**Status:** Accepted (KC-022)  
**Date:** 2026-07-25  
**Supersedes:** Static profile → provider binding for runtime selection  
**Does not modify:** KC-021 certification tags; Protocol V1 wire

## Context

KC-019/020/021 established CIAL with mock + OpenAI-compatible providers and a staging live gate. Profiles such as `research` still resolved to a hardcoded provider/model pair. That couples Computer/operators to vendors and blocks multi-capability routing.

## Decision

Introduce **AIR** as a deterministic, policy-driven router:

1. Computer requests **capabilities** (and optional named profile), never `provider=` / `model=`.
2. Providers advertise capabilities via registered descriptors.
3. AIR selects exactly one provider/model using a fixed order:
   required capabilities → health → policy → cost → latency → stable tiebreak.
4. Fail closed on capability miss — never silently pick an incapable model.
5. Every decision is audited (no prompts) and metered.

Profiles become **requirement policies**, not vendor bindings.

## Consequences

- New package: `cobra_core.air`
- `CialEngine` uses AIR by default (`AIR_ENABLED=true`); legacy `DeterministicRouter` remains for `AIR_ENABLED=false` and `MANUAL` policy.
- Future providers require registration only (descriptor + CIAL provider), not router edits.
- No autonomous learning, billing, or production enablement in this ADR.

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Keep hardcoded profile→vendor | Violates provider-neutral Computer contract |
| Soft fallback to any healthy model | Unsafe; capability miss must fail closed |
| ML / self-learning router | Out of scope; must stay deterministic and human-governed |
