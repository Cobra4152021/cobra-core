# Runtime Policy Profiles

Data-driven runtime profiles live under `runtime_policies/`.

| Profile | Purpose |
| --- | --- |
| `deterministic-short` | Short deterministic answers |
| `deterministic-investigation` | Higher output budget for investigation |
| `structured-json` | JSON parseable outputs |
| `long-document-analysis` | Long-doc diagnostics |
| `thinking-diagnostic` | Thinking-enabled diagnostic runs |

Profiles define max tokens, temperature, seed policy, thinking policy, parser, evidence standard, and resource guards.

**Important:** New profiles are **not** applied retroactively to the official CobraBench v0.1 baseline (`20260722T200000Z-8bba5e01`).
