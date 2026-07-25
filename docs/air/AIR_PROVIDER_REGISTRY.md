# AIR Provider Registry

## Registration model

Future providers require **registration only** — no AdaptiveRouter code changes.

1. Implement a CIAL `Provider` (generate + health).
2. Advertise an AIR `ProviderDescriptor` with one or more `ModelDescriptor`s.
3. Register both when the deployment gate allows (e.g. live OpenAI only when staging live gate is open).

## Descriptor fields

### Provider

| Field | Description |
|-------|-------------|
| `provider_id` | Stable id (`mock`, `openai`, …) |
| `display_name` | Human label |
| `models` | Nested model descriptors |
| `enabled` | Soft disable switch |

### Model

| Field | Description |
|-------|-------------|
| `provider_id` / `model_id` | Identity |
| `capabilities` | Advertised AIR capabilities |
| `estimated_cost` | `low` \| `normal` \| `high` \| `unknown` |
| `latency` | `fast` \| `normal` \| `slow` |
| `health` | CIAL `HealthState` |
| `requires_live` | True if external live vendor |
| `enabled` | Soft disable |

## Built-in catalog (KC-022)

### mock

- Always registered.
- Capabilities: text, offline, reasoning, summarization, classification, structured_output, coding, research, translation, long_context.
- Cost: low · Latency: fast · Health: healthy · `requires_live=false`
- **Does not** advertise vision / ocr / audio / video / agents.

### openai (OpenAI-compatible)

- Registered **only** when `CIAL` live gate is open (`can_use_live_provider`).
- Default model id from `OPENAI_MODEL` (certified staging: `gpt-5.4-mini`).
- Capabilities: text, reasoning, vision, ocr, summarization, classification, structured_output, coding, research, translation, long_context.
- Cost: low · Latency: normal · `requires_live=true`

## Example descriptor (conceptual)

```yaml
provider: openai
models:
  - id: gpt-5.4-mini
    supports: [reasoning, vision, ocr, structured_output]
    estimated_cost: low
    latency: medium   # mapped to LatencyClass.normal
    availability: healthy
```

## Adding a provider later

```python
from cobra_core.air.registry import DescriptorRegistry
from cobra_core.air.types import ModelDescriptor, ProviderDescriptor, CostClass, LatencyClass
from cobra_core.air.capabilities import AirCapability
from cobra_core.cial.health import HealthState

reg = DescriptorRegistry()
reg.register_provider(
    ProviderDescriptor(
        provider_id="example",
        display_name="Example",
        models=(
            ModelDescriptor(
                provider_id="example",
                model_id="example-1",
                capabilities=frozenset({AirCapability.TEXT, AirCapability.REASONING}),
                estimated_cost=CostClass.NORMAL,
                latency=LatencyClass.NORMAL,
                health=HealthState.HEALTHY,
            ),
        ),
    )
)
```

No router modifications required.
