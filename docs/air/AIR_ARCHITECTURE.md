# AIR Architecture

## Position in the stack

```
Computer  →  Protocol V1  →  CialEngine  →  AIR  →  Provider.generate()
                 (no provider/model)         │
                                             ├─ DescriptorRegistry
                                             ├─ AirPolicyConfig
                                             ├─ AdaptiveRouter
                                             ├─ AirAuditLog
                                             └─ AirMetrics
```

Computer never selects a provider or model. It requests capabilities (directly or via a named profile). AIR returns one decision; CIAL executes generation through the registered provider.

## Packages

| Module | Role |
|--------|------|
| `air.capabilities` | Capability catalog enum |
| `air.types` | `AirRequest`, `AirDecision`, descriptors |
| `air.profiles` | Named profiles → requirements |
| `air.registry` / `air.catalog` | Provider/model registration |
| `air.policy` | Human-governed policy config |
| `air.router` | Deterministic selection |
| `air.audit` / `air.metrics` | Observability (no prompts) |
| `air.bridge` | CIAL config → catalog/request |

## Request contract

```json
{
  "task": "investigation",
  "capabilities": ["reasoning", "vision"],
  "priority": "normal",
  "budget": "low",
  "latency": "normal"
}
```

Optional: `profile_id` expands to the same shape via `air.profiles`.

## Decision contract (audit-safe)

- profile, task, requested capabilities
- selected provider + model
- reason, health snapshot
- estimated cost class, latency class
- routing timestamp, policy id

**Never recorded:** prompts, messages, API keys, tokens.

## Live gate interaction (KC-021 preserved)

- OpenAI descriptors are registered in AIR **only** when `can_use_live_provider` is true.
- Research profile with live gate closed → AIR selects mock; engine records `profile_live_unavailable_use_offline`.
- Production remains disabled (`APP_ENV=production` never opens the live gate).

## Extension path

1. Register capability (if new).
2. Register provider descriptor + models.
3. Register CIAL provider implementation.
4. Optionally tune `config/air/default_policy.json` / `AIR_POLICY_PATH`.

No `AdaptiveRouter` code changes required for new vendors.
