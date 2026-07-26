# Evidence Integrity Policy

| State | Meaning |
|-------|---------|
| `verified` | Explicit verified or integrity hash present without mismatch |
| `unverified` | No hash / explicit unverified |
| `mismatch` | Hash mismatch — always excluded |
| `unavailable` | Integrity unavailable |

Defaults: `KEF_ALLOW_UNVERIFIED_INTEGRITY=false`. Required refs that are unverified or mismatched fail closed before AIR.
