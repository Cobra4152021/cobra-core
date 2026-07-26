# Benchmark Datasets

## Format

Each dataset is versioned (`dataset_id` + `version`) and contains cases with:

- `evidence` — expected evidence types / ref ids
- `gold.findings` — expected findings
- `gold.citations` — expected citation labels
- `gold.confidence_min` / `confidence_max`
- `gold.structured_fields` — skill-specific schema expectations
- `gold.summary_contains` — summary fragments
- `gold.expect_missing_evidence` — fail-closed path

Datasets are validated by `validate_dataset()` before registration.

## Built-in datasets (v1.0.0)

| Dataset ID | Skill |
|------------|--------|
| `vehicle_damage_v1` | `vehicle_damage_assessment` |
| `policy_review_v1` | `policy_compliance_review` |
| `contract_analysis_v1` | `contract_analysis` |
| `budget_analysis_v1` | `budget_analysis` |
| `timeline_v1` | `timeline_construction` |
| `evidence_summary_v1` | `evidence_summary` |
| `document_comparison_v1` | `document_comparison` |

Defined in `src/cobra_core/benchmark/datasets/builtin.py`.

## Extending

1. Author a dict matching `dataset_from_dict()` schema, **or** construct `BenchmarkDataset` / `BenchmarkCase`.
2. Bump `version` when gold answers change.
3. `DATASET_REGISTRY.register(dataset)`.

## Isolation

Benchmark datasets never seed production Evidence Vault or approval queues.
