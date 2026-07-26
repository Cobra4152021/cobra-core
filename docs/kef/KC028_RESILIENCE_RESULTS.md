# KC-028 Resilience Results

## Local deterministic adapter (PASS)

| Case | Result |
|------|--------|
| Timeout then success | PASS |
| Timeout exhaustion | PASS |
| 401 / 403 no retry success path | PASS |
| Distinct `evidence_vault` circuit key | PASS (implementation) |

## Staging

Vault health degraded / lookup timeouts observed from Core Containers — not certified as healthy connector resilience in live staging.
