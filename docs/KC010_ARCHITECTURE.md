# KC-010 — Cobra Enterprise Platform Architecture

**Status:** Alpha (v0.1.0)  
**Branch:** `kc-010-enterprise-core`

## Overview

KC-010 adds the **Cobra Enterprise Platform** pure TypeScript pack to cobra-core. The pack lives at the top level (`cobra/src/enterprise/`) as a sibling to `investigator/`, providing organization structure, SSO/SCIM helpers, policy RBAC, approvals, collaboration, audit center, AI governance, BYOM routing, secrets metadata, deployment profiles, data governance, licensing, and enterprise observability — without network I/O.

## Module Layout

```
cobra/src/enterprise/
├── types.ts           # Shared enterprise types
├── orgStructure.ts    # Org tree build/flatten/validate
├── sso.ts             # SSO normalize, authorize stub, validate
├── scim.ts            # SCIM user map, validate, role mapping
├── policyRbac.ts      # PolicyEngine (deny-by-default RBAC)
├── approvals.ts       # Approval FSM + chain builder
├── collaboration.ts   # Activity feed, mentions, assignments
├── auditCenter.ts     # Audit categorize, filter, facets
├── aiGovernance.ts    # Model allowlist, token/cost budgets, retention
├── byom.ts            # BYOM normalize, validate, routeModel
├── secrets.ts         # Redact, scope validate, rotation due
├── deployment.ts      # DEPLOYMENT_PROFILES (6 profiles)
├── dataGovernance.ts  # Retention, legal hold, soft delete
├── licensing.ts       # Entitlement, seat, pack license checks
├── observability.ts   # aggregateEnterpriseMetrics
├── domain.ts          # ENTERPRISE_DOMAIN metadata
└── index.ts           # Public re-exports
```

## Package Export

Enterprise is exported from the cobra package root:

```typescript
import {
  PolicyEngine,
  ENTERPRISE_DOMAIN,
  DEPLOYMENT_PROFILES,
} from "@cobra-core/knowledge-engine";
```

Or via direct path after build:

```typescript
import { buildOrgTree } from "./enterprise/index.js";
```

## Deployment Profiles

| ID | Internet | BYOM | SSO | Max Nodes |
|----|----------|------|-----|-----------|
| `cloud` | yes | yes | yes | unlimited |
| `hybrid` | yes | yes | yes | unlimited |
| `air_gapped` | no | yes | yes | unlimited |
| `on_premises` | no | yes | yes | unlimited |
| `single_node` | no | no | no | 1 |
| `ha` | no | yes | yes | unlimited |

## Policy RBAC

`PolicyEngine.evaluatePolicy()` accepts:

- `actorRole`, `action`, `resourceType`, `resourceId`, `orgId`
- optional `domainPack`

Resource types: `report`, `sdk`, `studio`, `marketplace`, `domain_pack`, `investigation`.

Deny rules take precedence over allow rules; default role matrix applies when no explicit rule matches.

## Feature Flags

- `ENTERPRISE_SSO`
- `ENTERPRISE_SCIM`
- `ENTERPRISE_POLICY_RBAC`
- `ENTERPRISE_APPROVALS`
- `ENTERPRISE_AI_GOVERNANCE`
- `ENTERPRISE_BYOM`
- `ENTERPRISE_AUDIT_CENTER`
- `ENTERPRISE_DEPLOYMENT_PROFILES`

## Disclaimers

All enterprise outputs should carry `ENTERPRISE_DOMAIN.defaultDisclaimers` — governance reduces risk but does not constitute legal compliance, security certification, or production approval by itself.

## Tests

`cobra/tests/enterprise.test.ts` covers:

- Org nesting (tree, flatten, cycle detection)
- SSO authorize stub (deterministic)
- SCIM user map + role mapping
- Policy deny cross-resource
- Approval FSM
- AI governance model block
- BYOM route
- Licensing seat check
- Audit filter + facets

## Related Docs

- `docs/KC010_FINAL_REPORT.md` — delivery report (pending verification)
