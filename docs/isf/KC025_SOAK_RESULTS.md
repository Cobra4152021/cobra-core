# KC-025 — Controlled Soak Results

Workload mix: 25% evidence_summary, 20% timeline, 15% policy, 15% document_comparison,  
15% vehicle_damage (expected fail offline), 10% expected failures.

| N | Status | Notes |
|---|--------|-------|
| 10 | _pending staging_ | |
| 25 | _pending staging_ | |
| 50 | _pending staging_ | |

Stop conditions: credential/evidence leakage, invalid schema accepted, approval bypass,  
unexpected provider fallback, audit omission, abnormal cost, rollback failure.

Harness: `python scripts/kc025/staging_cert.py --soak N`
