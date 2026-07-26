# Evidence Model

## EvidenceItem

| Field | Description |
|-------|-------------|
| `id` | Opaque evidence identifier |
| `type` | `EvidenceKind` (policy, image, budget, …) |
| `source` | Connector / origin label |
| `title` / `summary` | Safe metadata (no document body) |
| `content_reference` | Handle for later read (not body) |
| `created_time` / `modified_time` | Optional ISO timestamps |
| `author` | Optional |
| `confidence` | Connector confidence 0–1 |
| `integrity_hash` | Content fingerprint (never the body) |
| `metadata` | Bounded key/values (no text/body) |
| `permissions` | Visibility, classification, roles |
| `retrieval_score` | Deterministic rank score |
| `skill_evidence_type` | ISF `EvidenceType` when known |

## Supported kinds

`policy`, `report`, `document`, `pdf`, `docx`, `spreadsheet`, `email`, `image`, `audio_transcript`, `video_transcript`, `timeline`, `case_note`, `budget`, `contract`

Reserved: `database`, `body_camera`, `dispatch`, `gps`

## ISF mapping (examples)

| Skill requirement | KEF kind |
|-------------------|----------|
| `vehicle_photos` | `image` |
| `policy_document` | `policy` |
| `budget_spreadsheet` | `budget` |
| `contract_document` | `contract` |
| `case_notes` | `case_note` |

Bodies are never stored on `EvidenceItem` or in KEF audit logs.
