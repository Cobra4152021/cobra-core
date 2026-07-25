# KC-019 — Provider Contract

## Interface

`InferenceProvider` (`src/cobra_core/cial/provider.py`) requires:

| Member | Purpose |
|--------|---------|
| `provider_id` | Stable adapter id (e.g. `mock`) |
| `list_models()` | Contributes `ModelRecord` entries |
| `capabilities()` | Aggregate capability hint |
| `health()` | Aggregate provider health |
| `readiness_check()` | Optional preflight |
| `generate(GenerateRequest)` | Typed request → typed `InferenceResult` |

## Rules

1. Do not expose provider SDK objects outside the adapter.
2. Do not leak provider-specific fields into Protocol V1 responses.
3. Map failures to `CialError` / `CialErrorCode`; Core maps those to Protocol codes.
4. Phase 1 adapters must not perform live network calls.

## Model registry fields

Each `ModelRecord` declares at least:

`provider_id`, `model_id`, `display_name`, `enabled`, `capabilities`,
`context_window`, `max_output_tokens`, `supports_json`, `supports_tools`,
`supports_vision`, `supports_streaming`, `quality_tier`, `latency_tier`,
`estimated_input_cost`, `estimated_output_cost`, `revision`, `metadata`, `health`.

Costs may be `None` (unknown). No live pricing lookup in Phase 1.

## Capabilities

Typed enum: `text`, `reasoning`, `json`, `tools`, `vision`, `streaming`, `research`.

Routing may require one or more capabilities (`RoutingRequest.required_capabilities`).

## Mock provider

- `provider_id = mock`
- Default `model_id = cobra-core-qwen3-8b` (Protocol V1 wire identity)
- Backend: `cobra_core.protocol_v1.inference.mock_complete`
- Content prefix `[mock] …` preserved for Internal Alpha / tests
