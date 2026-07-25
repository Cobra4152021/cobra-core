# ISF Architecture

## Flow

```
Computer
   ↓  SkillRequest(skill_id, evidence[])
SkillEngine
   ↓  SkillRegistry → SkillManifest
   ↓  evidence check (fail closed if missing)
   ↓  capability expansion
AIR (AdaptiveRouter)
   ↓  provider/model decision
Provider (optional inference)
   ↓
Structured SkillResult (schema-validated)
```

Computer never selects provider/model and should not send raw capability lists as the primary contract.

## Packages

| Module | Role |
|--------|------|
| `isf.manifest` | SkillManifest contract |
| `isf.registry` | Registration surface |
| `isf.evidence` | Evidence types + checks |
| `isf.schemas` | Pydantic structured outputs |
| `isf.confidence` | Thresholds / disposition |
| `isf.engine` | Expand → AIR → typed result |
| `isf.audit` | Safe skill audit (no prompts) |
| `isf.skills` | Built-in self-registering manifests |

## Principles

- Provider-neutral / model-neutral
- Policy-driven via manifests
- Fail closed on missing evidence or AIR capability miss
- Confidence must not invent certainty
- Human review when below threshold
