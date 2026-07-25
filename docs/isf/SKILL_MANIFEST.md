# Skill Manifest

Each skill declares a machine-readable manifest:

| Field | Description |
|-------|-------------|
| `id` | Stable skill id (snake_case) |
| `title` | Human title (e.g. VehicleDamageAssessment) |
| `version` | Semver string |
| `description` | Short purpose |
| `required_capabilities` | AIR capabilities (all required) |
| `optional_capabilities` | Soft preferences (not forced into AIR request) |
| `required_evidence_types` | Evidence kinds Computer must supply |
| `supported_profiles` | Allowed CIAL/AIR profile ids |
| `confidence_policy` | Minimum confidence + caps |
| `output_schema_id` | Key into structured schema registry |

## Example — VehicleDamageAssessment

```text
id: vehicle_damage_assessment
required_capabilities: vision, reasoning, structured_output
required_evidence: vehicle_photos
minimum_confidence: 0.75
output: VehicleDamageAssessmentOutput
```

## Validation

Manifests without required capabilities or without a registered output schema are rejected at construction (`manifest_invalid`).
