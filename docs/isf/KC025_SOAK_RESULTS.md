# KC-025 — Controlled Soak Results

**Environment:** staging offline (`CIAL_LIVE_PROVIDER_ENABLED=false`, mock catalog)  
**Harness:** `python scripts/kc025/staging_cert.py --soak N`  
**No OpenAI traffic during offline soak.**

Workload mix: 25% evidence_summary, 20% timeline, 15% policy, 15% document_comparison,  
15% vehicle_damage (expected fail — no vision), 10% expected failures.

| N | Successes | Expected fail | Unexpected | Schema-valid | Repair | Human review | Providers | p50 ms | p95 ms | Audit ok |
|---|-----------|---------------|------------|--------------|--------|--------------|-----------|--------|--------|----------|
| 10 | 6 | 4 | 0 | 6 | 0 | 6 | mock:6 | 78.8 | 137.4 | 10 |
| 25 | 19 | 6 | 0 | 19 | 0 | 19 | mock:19 | 80.6 | 96.1 | 25 |
| 50 | 40 | 10 | 0 | 40 | 0 | 40 | mock:40 | 78.4 | 91.7 | 50 |

Confidence avg (mock path): **0.45**  
Model (mock): `cobra-core-qwen3-8b`  
Tokens / cost: not applicable (mock; no live calls)  
Governance failures: **0**  
Stop conditions: none triggered.
