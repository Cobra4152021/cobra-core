# Retrieval Policy

## Modes

| Mode | Behavior |
|------|----------|
| `exact` | Resolve provided ref ids (default for skill execution) |
| `metadata` | Filter by metadata across connectors |
| `registry` | Connector registry search |
| `hybrid` | Combine lookup + search |
| `semantic` | **Disabled** in KC-027 (fail closed) |

## Skill gate

Before AIR:

1. Resolve refs via connectors (optional request seed into memory)
2. Permission filter (denied items audited, not returned)
3. Deduplicate by integrity hash / canonical id
4. Rank deterministically
5. Validate required skill evidence types (+ document_comparison cardinality)
6. Fail with typed `missing_required_evidence` if gaps remain

## Ranking factors (no ML)

1. Explicit request match
2. Required type match
3. Metadata match
4. Type priority
5. Connector confidence
6. Manual priority metadata
7. Freshness bonus

## Max results

Configurable via `KEF_MAX_RESULTS` (default 25).
