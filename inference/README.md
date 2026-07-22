# Inference

Provider-neutral inference stubs.

- Code: `src/cobra_core/inference/`
- Phase 1 does not assume vLLM, TGI, llama.cpp, OpenAI-compatible APIs, or any GPU vendor.
- `InferenceRunner` refuses to run until a provider backend is configured.
