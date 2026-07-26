# KEF Architecture

## Flow

```
Computer (opaque evidence handles)
    ↓
ISF SkillEngine
    ↓
KEF Gateway (retrieve_for_skill)
    ↓ resolve → permission filter → dedupe → rank → cite
    ↓ fail closed on missing required evidence
AIR → RRF → CIAL → Provider
    ↓
SkillResult (+ citations) → pending_approval
```

## Package

`src/cobra_core/kef/`

| Module | Role |
|--------|------|
| `types.py` | `EvidenceItem`, `Citation`, retrieval contracts |
| `normalizer.py` | Connector-native / EvidenceRef → `EvidenceItem` |
| `resolver.py` | Multi-connector lookup + request seed |
| `retrieval.py` | `KefGateway` orchestration |
| `ranking.py` | Deterministic scoring (no ML) |
| `deduplication.py` | Hash / canonical collapse |
| `citation.py` | `EV-xxx` labels + output attach |
| `security.py` | Permission / classification checks |
| `registry.py` | Connector registry |
| `connectors/` | `memory`, `mock`, `evidence_vault` stub |
| `audit.py` / `metrics.py` | Safe observability |

## Gates

| Env | Default | Effect |
|-----|---------|--------|
| `KEF_ENABLED` | true | When false, ISF uses pre-KEF type-gap checks |
| `KEF_MAX_RESULTS` | 25 | Cap ranked results |
| `KEF_ALLOW_REQUEST_SEED` | true | Normalize Computer refs into MemoryConnector |
| `KEF_SEMANTIC_ENABLED` | false | Must stay false (out of scope) |
