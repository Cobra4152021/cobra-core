# KC-003 — Security

## ACL model

Every object carries `orgId`, optional `projectId`, `ownerUserId`, `visibility`, optional `allowUserIds`.

Visibility: `private` | `project` | `organization` | `public`.

## Rules

- Deny by default (`canRead` / `canWrite`).  
- **No cross-project leakage** — project visibility requires membership.  
- Org mismatch always denied.  
- Citations require real evidence fields; unknown citation IDs rejected.  

## Production note

When mounting in Cobra Computer, reuse existing session/org auth; map to `AuthContext`. Do not weaken Benchmark Lab or chat RBAC.
