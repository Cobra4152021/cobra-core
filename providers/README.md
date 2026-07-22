# Providers

Provider-neutral notes for evaluation targets.

| Provider | Role in Phase 1 |
| --- | --- |
| `qwen/` | First evaluation target (interface placeholder) |
| `mistral/` | Supported family placeholder |
| `gemma/` | Supported family placeholder |

Executable interfaces live in `src/cobra_core/providers/`.

Phase 1 modules do **not**:

- download model weights
- assume a cloud inference host
- assume a GPU vendor
- assume vLLM / TGI / llama.cpp / OpenAI-compatible specifics

Configure a concrete backend only when baseline evaluation begins.
