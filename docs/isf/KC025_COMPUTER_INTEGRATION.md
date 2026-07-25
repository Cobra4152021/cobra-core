# KC-025 — Computer → ISF Integration

**Branch:** `kc-025-isf-staging-cert`  
**Base:** `dde59ec`  
**Production:** disabled  

## Contract

Computer submits (Protocol V1-compatible body to `POST /isf/execute`):

| Field | Required | Notes |
|-------|----------|-------|
| `skill_id` | yes | Registry lookup |
| `skill_version` | no | Exact or same major.minor with patch ≤ registered |
| `evidence` | skill-dependent | `{evidence_type, ref_id, metadata?}` |
| `profile_id` / `request_profile` | no | Default `default` |
| `inputs` / `task` | no | Bounded task inputs |
| `correlation_id` | no | Propagated into audit |

Computer must **not** submit: `provider_id`, `model_id`, OpenAI fields, raw `capabilities`, AIR routing instructions.

## Adapter

`src/cobra_core/isf/computer_adapter.py` — `ComputerIsfAdapter`

1. Reject forbidden provider/model/capability fields  
2. Map evidence refs (hashes text; never stores bodies)  
3. Resolve skill + version compatibility  
4. Execute via `SkillEngine`  
5. Return proposal with `status=pending_approval` (or `failed`)

Additive envelope:

```json
{
  "ok": true,
  "proposal": {
    "status": "pending_approval",
    "skill_id": "...",
    "skill_version": "...",
    "structured_result": {},
    "confidence": 0.0,
    "needs_human_review": true,
    "human_approval_required": true
  },
  "extensions": { "isf": { } }
}
```

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/isf/execute` | Computer skill execution |
| GET | `/isf/skills` | Registered skills (safe metadata) |
| GET | `/isf/audit` | Bounded audit |
| GET | `/isf/metrics` | JSON metrics snapshot |
| GET | `/isf-gate` | Worker boolean probe |
| GET | `/health` → `isfGate` | Edge diagnostic |

## Feature gate

`ISF_ENABLED` (default `true`). When `false`, `/isf/execute` returns `isf_disabled` (503); legacy Computer → Core → AIR chat path remains.
