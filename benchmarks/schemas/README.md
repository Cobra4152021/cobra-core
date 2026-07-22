# JSON Schemas

Machine-readable companions to the Pydantic models in `src/cobra_core/schemas/`.

| File | Model |
| --- | --- |
| `model_manifest.schema.json` | ModelManifest |
| `benchmark_case.schema.json` | BenchmarkCase |
| `evaluation_run.schema.json` | EvaluationRun |

Runtime validation uses Pydantic. These JSON Schema files document the contract for non-Python tooling.
