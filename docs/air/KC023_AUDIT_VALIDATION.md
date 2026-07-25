# KC-023 — Routing Audit Validation

## Required fields (success)

Verified on staging `GET /air/audit` and decision payloads from `POST /air/route`:

| Field | Present |
|-------|---------|
| policy_id | yes |
| profile | yes |
| requested_capabilities | yes |
| selected_provider | yes |
| selected_model | yes |
| selection_reason | yes |
| health_snapshot | yes |
| estimated_cost_class | yes |
| latency_class | yes |
| routing_timestamp | yes |
| correlation_id | yes (`x-request-id` / body) |

## Failures

Failure audits record `failure_code`, `failure_message`, capabilities, profile, correlation_id, and null selection fields. Phase 1 vision miss and Phase 2 policy exclusion both audited.

## Forbidden content

Never recorded:

- full prompt / messages
- secret values / API keys
- provider credentials
- full evidence text
- raw provider response bodies

Prometheus `/metrics` AIR series use **bounded** labels only (`provider`, `model` allow-lists). Correlation IDs are not metric labels.

## Telemetry counters observed

`air_routing_total`, `air_routing_success_total`, `air_routing_failure_total`, `air_provider_selection_total`, `air_model_selection_total`, `air_no_capability_match_total`, `air_provider_unhealthy_total`, `air_policy_exclusion_total`, `air_fail_closed_total`, `air_routing_latency_ms_*`.
