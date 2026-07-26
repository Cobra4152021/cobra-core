# KC-028 Security Results

## Local (PASS)

| Case | Result |
|------|--------|
| Permission denied excluded from context | PASS (`tests/test_kef_vault.py`) |
| Hash mismatch excluded | PASS |
| No request seed when disabled | PASS |
| Invented citation rejected | PASS |
| Token never in audit/metrics | PASS (static + unit) |

## Staging

Blocked on Core→Vault connectivity. Workstation Vault auth with staging key succeeds; unauthorized public `/api/health` without key returns 403.
