# KC-019 — CIAL Architecture (Phase 1)

## Why CIAL exists

Cobra Computer must talk only to Cobra Core. Core needs a stable,
provider-independent inference interface so future models (OpenAI, Gemini,
Anthropic, Cloudflare AI, local) can be added without changing Protocol V1
or Computer adapters.

CIAL (Cobra Intelligence Abstraction Layer) is that interface.

## Trust boundaries

```
Cobra Computer
      |
      v
Cobra Core Protocol V1  (frozen wire schemas)
      |
      v
CIAL  (internal contracts only)
      |
      +-- Mock Provider (Phase 1)
      +-- Future providers (later phases)
```

- **Computer → Core:** Protocol V1 only. No CIAL types on the wire.
- **Core → CIAL:** Internal Python contracts (`GenerateRequest`, `InferenceResult`, registries).
- **CIAL → Provider adapters:** Adapters own SDK objects; nothing SDK-shaped escapes.
- **Credentials:** Provider secrets stay in Core process env (never Computer, never Protocol V1 responses). Phase 1 adds **no** secrets.

## Package layout

```
src/cobra_core/cial/
  __init__.py
  types.py          # requests, results, ModelRecord, RoutingPolicy
  capabilities.py
  errors.py         # taxonomy + Protocol V1 code map
  provider.py       # InferenceProvider Protocol
  registry.py       # ModelRegistry / ProviderRegistry
  router.py         # DeterministicRouter
  config.py         # CIAL_* env loading
  health.py
  engine.py         # route + generate orchestration
  providers/
    mock.py         # wraps protocol_v1.inference.mock_complete
```

**Decision:** New `cobra_core.cial` package (not the lab `providers/` placeholders)
keeps Protocol V1 and research-lab provider scaffolds separate.

## Mock migration

- Existing `mock_complete` remains the deterministic backend.
- `MockProvider` wraps it behind `InferenceProvider`.
- `InferenceService` uses `CialEngine` when `CIAL_ENABLED=true` (default) and
  `COBRA_INFERENCE_MODE` is `mock` / `echo` / `test`.
- Wire model identity stays `cobra-core-qwen3-8b`.
- Escape hatch: `CIAL_ENABLED=false` calls `mock_complete` directly.

## Observability (internal)

`ServiceOutcome` may carry `cial_*` fields for operators/tests. Handlers do
**not** serialize them into Protocol V1 JSON. Never log prompts, evidence,
secrets, or full model responses.

## Known limitations (Phase 1)

- No live network providers.
- No automatic fallback execution (`cial_fallback_count` always 0).
- No dynamic pricing.
- Local Qwen path bypasses CIAL (unchanged).
- Streaming transport unchanged.

## Next phase

Register real provider adapters behind feature flags, add fallback manager,
and keep mock as the Internal Alpha default until explicitly certified.
