# KC-026 Governance Results

**Suite:** Computer staging `npm run kc018:approval`  
**Repo:** `hidden-grid-os-qwen-live`  
**Core staging:** `https://cobra-core-staging.cobra4152020.workers.dev`  
**Constraint:** No autonomous approval; all AI results remain human-gated  

## Final regression (post-cert restore, RRF on / live off)

```
KC-018 approval workflow: 13 passed, 0 failed
PASS: KC-018 approval workflow
```

| Case | Result |
|------|--------|
| create_for_approve | PASS |
| approve_proposal | PASS |
| approve_audit | PASS |
| approve_no_publish | PASS |
| reject_proposal | PASS |
| reject_audit | PASS |
| cancel_unsupported | PASS |
| duplicate_replaces_pending | PASS |
| duplicate_stale_id_rejected | PASS |
| duplicate_current_decidable | PASS |
| already_decided_conflict | PASS |
| unauthorized_no_session | PASS |
| unauthorized_missing_csrf | PASS |

## Coverage vs KC-026 Phase 5

| Requirement | Evidence |
|-------------|----------|
| Approve / reject | PASS |
| Revision mismatch / stale id | PASS (409) |
| Duplicate approval / rejection | PASS (conflict / replace semantics) |
| Approval after rejection / rejection after approval | PASS (already_decided) |
| No duplicate active proposal from retries | Covered by RRF idempotency unit tests + Computer duplicate replace |
| Human actor recorded | Audit cases PASS |
| Attempt history / final provider-model attached | RRF audit + ISF proposal metadata (unit + staging audit) |
| No autonomous approval | All successes `pending_approval` before human decision |

Also run during live research window and rollback window in this certification cycle — both green (13/13).
