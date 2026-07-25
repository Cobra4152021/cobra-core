# KC-025 — ISF Audit Validation

Every execution audit record includes (safe fields only):

- `correlation_id`, `skill_id`, `skill_version`, `manifest_version`
- `requested_profile`
- `required_capabilities`, `optional_capabilities_used`
- `required_evidence_types`, `evidence_validation_result`
- `selected_provider`, `selected_model`, `routing_reason`
- `schema_name`, `schema_validation_result`, `repair_attempt_count`
- `confidence`, `confidence_threshold`, `needs_human_review`
- `execution_status`, `timestamp`

**Never stored:** prompts, API keys, credentials, raw evidence bodies, full provider responses.

## Telemetry (bounded labels)

`isf_execution_total`, `isf_execution_success_total`, `isf_execution_failure_total`,  
`isf_skill_selection_total`, `isf_missing_evidence_total`,  
`isf_schema_validation_failure_total`, `isf_schema_repair_total`,  
`isf_schema_repair_failure_total`, `isf_low_confidence_total`,  
`isf_human_review_required_total`, `isf_execution_latency_ms`

Labels: `skill_id`, `status`, `provider_id`, `schema_result` only.
