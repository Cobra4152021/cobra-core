# Plugin Types

Types are registry-based. New types require a `PluginType` enum value and a `TYPE_PERMISSIONS` mapping.

| Type | Permission | Purpose |
|------|------------|---------|
| `isf_skill` | `register_skill` | ISF skill declaration payload |
| `kef_connector` | `register_connector` | KEF connector declaration |
| `workflow_template` | `register_workflow` | Workflow template payload |
| `case_template` | `register_case_template` | Case template payload |
| `benchmark_dataset` | `register_dataset` | Benchmark dataset payload |
| `report` | `register_report` | Report template payload |
| `validator` | `register_validator` | Validator declaration |
| `policy` | `register_policy` | Policy declaration |

Unsupported `plugin_type` values fail closed at manifest parse time.
