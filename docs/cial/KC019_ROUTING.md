# KC-019 — Routing

## Policies

| Policy | Behavior (Phase 1) |
|--------|--------------------|
| `default` | Prefer `CIAL_DEFAULT_MODEL` / request preferred id among eligible |
| `lowest_cost` | Minimize estimated input+output cost (`None` → +∞) |
| `lowest_latency` | Prefer `LatencyTier.FAST` → `STANDARD` → `SLOW` |
| `highest_quality` | Prefer `PREMIUM` → `HIGH` → `STANDARD` → `LOW` |
| `reasoning` | Require `Capability.REASONING`, then highest quality |
| `research` | Require `Capability.RESEARCH`, then highest quality |
| `manual` | Exact `provider_id` + `model_id`; validate eligibility |

## Eligibility

A model is eligible when:

1. `enabled is True`
2. Health is not `unavailable` or `disabled`
3. Required capabilities ⊆ model capabilities

## Health behavior

| State | Auto policies | Manual |
|-------|---------------|--------|
| `healthy` | Eligible (preferred) | Allowed |
| `unknown` | Eligible | Allowed |
| `degraded` | Eligible, ranked after healthy/unknown on ties | Allowed |
| `unavailable` | Excluded | Rejected (`provider_unavailable`) |
| `disabled` | Excluded | Rejected (`model_disabled`) |

**Degraded:** Still selectable so Internal Alpha can continue under partial
degradation; operators should treat `cial_health_state=degraded` as a signal,
not silence.

## Tie-breakers

After policy score, sort by:

1. Health preference (`healthy` < `unknown` < `degraded`)
2. `provider_id` ascending
3. `model_id` ascending

## Fallback

Automatic fallback execution is **out of scope** for Phase 1.
`cial_fallback_count` is always `0`. Reserved for a later phase.
