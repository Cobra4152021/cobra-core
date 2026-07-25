# AIR Policy

## Principles

- **Human-governed** — operators edit policy config; the router does not self-learn.
- **Deterministic** — same registry + request + policy ⇒ same decision.
- **Fail closed** — no silent vendor substitution on capability miss.

## Fixed evaluation order

1. **Required capabilities** — model must support the full set.
2. **Health** — exclude `unavailable` / `disabled`.
3. **Policy** — exclusions, live preference, operator provider preference.
4. **Cost** — prefer within requested budget class.
5. **Latency** — prefer models meeting requested latency class.
6. **Stable tiebreak** — `(provider_id, model_id)` lexicographic ascending.

## Built-in profile policies

| Profile | Requires live | Typical capabilities |
|---------|---------------|----------------------|
| `default` | no | text, offline |
| `offline` | no | text, offline |
| `research` | yes (when gate open) | reasoning, summarization, structured_output, research |
| `analysis` | no | reasoning, classification, structured_output |
| `coding` | no | coding, reasoning |

Profiles describe **requirements**, not vendors.

## Config surfaces

| Source | Purpose |
|--------|---------|
| `config/air/default_policy.json` | Default policy document |
| `AIR_POLICY_PATH` | Override policy JSON path |
| `AIR_POLICY_ID` | Override policy id label |
| `AIR_EXCLUDE_PROVIDERS` | Comma-separated hard exclusions |
| `AIR_ENABLED` | `true` (default) use AIR; `false` legacy router |

### Example policy JSON

```json
{
  "policy_id": "ops_v1",
  "prefer_live_when_required": true,
  "prefer_healthy_over_degraded": true,
  "provider_preference": {
    "openai": 10,
    "mock": 50
  },
  "excluded_providers": [],
  "excluded_models": []
}
```

Lower `provider_preference` values win (after health).

## Live preference

When the request metadata has `requires_live=true` and any live-capable candidate exists, offline-only models are dropped. If none exist and `allow_offline_fallback=true`, offline models remain eligible (KC-021 research rollback behavior).

## Failure policy

| Condition | `AirRoutingFailureCode` |
|-----------|-------------------------|
| No capability match | `no_capability_match` |
| No routable health | `no_healthy_candidate` |
| All excluded by policy | `policy_excluded` |
| Live required, unavailable, no fallback | `live_required_unavailable` |
| Empty registry | `empty_registry` |
