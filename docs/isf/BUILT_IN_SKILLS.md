# Built-in Investigation Skills

| Skill id | Title | Required capabilities | Required evidence |
|----------|-------|----------------------|-------------------|
| `vehicle_damage_assessment` | VehicleDamageAssessment | vision, reasoning, structured_output | vehicle_photos |
| `policy_compliance_review` | PolicyComplianceReview | reasoning, summarization, structured_output | policy_document |
| `contract_analysis` | ContractAnalysis | reasoning, summarization, structured_output | contract_document |
| `budget_analysis` | BudgetAnalysis | reasoning, classification, structured_output | budget_spreadsheet |
| `evidence_summary` | EvidenceSummary | summarization, reasoning, structured_output | evidence_bundle |
| `timeline_construction` | TimelineConstruction | reasoning, summarization, structured_output | timeline_source |
| `pattern_detection` | PatternDetection | reasoning, classification, structured_output | case_notes |
| `open_source_research` | OpenSourceResearch | research, reasoning, structured_output | open_source_query |
| `interview_summary` | InterviewSummary | summarization, reasoning, structured_output | interview_transcript |
| `document_comparison` | DocumentComparison | reasoning, summarization, structured_output | document_pair |

## VehicleDamageAssessment output fields

- `summary`
- `damage_locations`
- `severity`
- `structural_damage` / `structural_concerns`
- `repair_recommendations`
- `confidence`
- `missing_information`
- `recommended_next_steps`
- `needs_human_review`

## Evidence miss

If required evidence is absent, the engine returns status `missing_required_evidence` with a typed error payload — it does not silently proceed.
