# Phase 5B.2 Acceptance Checklist

| # | Criterion | Result |
| --- | --- | --- |
| 1 | Pre-flight green | PASS |
| 2 | ≤1 temporary GPU (plus allowed replace of unusable) | PASS |
| 3 | Cost < $10 (~$0.22 est.) | PASS |
| 4 | Frozen Core `00e4862b` deployed | PASS |
| 5 | Protocol V1 direct conformance | PASS |
| 6 | Authenticated HTTPS | PASS |
| 7 | Real inference | PASS |
| 8 | Computer staging connect | PASS |
| 9 | Admin-only access posture | PASS (adapter + flags) |
| 10 | Ordinary users cannot discover/invoke | PASS (adapter suite) |
| 11 | Organization isolation | PARTIAL — adapter/org patterns exist; live JWT harness unavailable |
| 12 | Request IDs end-to-end | PASS (Core + smoke) |
| 13 | Usage normalization | PASS |
| 14 | Latency normalization | PASS |
| 15 | Timeout/error normalization | PASS |
| 16 | One-shot stream compatibility | PASS |
| 17 | No fallback | PASS |
| 18 | No adaptive Core selection | PASS |
| 19 | Shadow false | PASS |
| 20 | Production unchanged | PASS |
| 21 | No secrets exposed | PASS |
| 22 | Evidence exported | PASS |
| 23 | Kill switch | PASS |
| 24 | Core disabled after testing | PASS |
| 25 | Credential invalidated | PASS |
| 26 | GPU terminated | PASS |
| 27 | Endpoint removed | PASS (tunnel 530 / pod gone) |
| 28 | Zero billable resources | PASS |
| 29 | Governance hashes unchanged | PASS |
| 30 | CobraBench prepared-not-run | PASS |
| 31 | Official score 0.840 | PASS |

Overall: **PASS** for Phase 5B.2 staging exercise with documented limitation on live Worker JWT org/admin session harness.
