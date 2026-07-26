# ADR-0013 — Multi-Organization & Tenant Framework (MOTF)

## Status

Accepted (KC-035)

## Context

Cobra Core previously operated as a single-organization investigation platform. Agencies need isolated tenants for users, cases, workflows, evidence references, plugins, benchmarks, operations, audit, and configuration — without federation or cross-agency sharing in this milestone.

## Decision

Add `cobra_core.organizations` as MOTF:

```
Cobra → Organization → Department → Users → Cases → Evidence → Workflows → Reports
```

MOTF owns:

- Organization + department models
- Scoped membership (roles do not transfer across orgs)
- Immutable resource ownership tagging
- Tenant isolation (default deny cross-org)
- Plugin / benchmark / workflow scoping
- Administrative case move (authz + audit)
- Per-org metrics and audit fields
- Tenant-aware ISPF authorization (`organization_id` / `department_id`)
- Authenticated HTTP under `/organizations/*`

MOTF does **not** own federation, cross-agency investigations, SSO, billing, branding, or production enablement.

## Consequences

- KC-034 `authorize()` accepts optional tenant context and denies cross-org resource access
- Global ISPF roles do not imply org membership; membership roles map to ISPF permissions within an org
- Production remains disabled; no automatic merge
