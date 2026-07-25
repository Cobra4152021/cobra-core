# AIR Capabilities

Machine-readable capabilities Computer may request. Vendors are never part of the request contract.

## Initial (KC-022)

| Capability | Meaning |
|------------|---------|
| `reasoning` | Multi-step / analytic reasoning |
| `vision` | Image understanding |
| `ocr` | Text extraction from images |
| `coding` | Code generation / editing assistance |
| `summarization` | Condensation of long text |
| `classification` | Labeling / triage |
| `translation` | Language translation |
| `structured_output` | JSON / schema-shaped answers |
| `long_context` | Large context windows |
| `offline` | Runnable without external live vendor |
| `text` | Baseline text completion |
| `research` | Investigation / research workloads |

## Future (registered, not required by initial profiles)

| Capability | Status |
|------------|--------|
| `audio` | Reserved |
| `video` | Reserved |
| `agents` | Reserved |

## Matching rule

A model is eligible only when **all** requested capabilities are a subset of its advertised set. Partial matches never win.

## Examples

**Investigation with vision**

```json
{
  "task": "investigation",
  "capabilities": ["reasoning", "vision"],
  "priority": "normal",
  "budget": "low",
  "latency": "normal"
}
```

With OpenAI registered → selects openai. With mock only → fail closed (`no_capability_match`).

**Offline default**

```json
{
  "task": "general",
  "capabilities": ["text", "offline"],
  "budget": "low",
  "latency": "fast"
}
```

Selects mock.
