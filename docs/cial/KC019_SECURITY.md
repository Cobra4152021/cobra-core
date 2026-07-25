# KC-019 — Security Notes

## Credential boundary

- Phase 1 introduces **no** API keys, OAuth tokens, or provider secrets.
- Future provider credentials must live only in Core process environment /
  secret stores — never in Computer, never in Protocol V1 payloads, never in
  CIAL registry metadata that is logged.

## Logging

Safe to log (when needed):

- `cial_provider_id`, `cial_model_id`, `cial_routing_policy`, `cial_route_reason`
- `cial_latency_ms`, `cial_fallback_count`, `cial_health_state`
- existing request IDs / proposal IDs / audit events

Never log:

- prompts / evidence content
- full model responses
- auth secrets / Bearer tokens
- provider API keys

## Production controls

CIAL does not weaken existing production hard blocks:

- `COBRA_CORE_ENABLED` kill switch remains authoritative for completions.
- Protocol version pins remain frozen.
- Production Computer must keep Core disabled until a future certification
  explicitly enables it.

## Error mapping

CIAL errors map into existing Protocol V1 codes (`provider_error`,
`model_unavailable`, `provider_disabled`, `rate_limited`, …) so Computer
clients do not need new wire error shapes.
