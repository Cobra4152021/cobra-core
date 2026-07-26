# ADR-0012 — Identity, Security & Policy Framework (ISPF)

## Status

Accepted (KC-034)

## Context

Cobra Core subsystems (Cases, Workflows, ISF, KEF, Plugins, Operations, Evidence Vault, Benchmark) need a single authorization origin. Authorization must not alter routing, workflows, or AI behavior.

## Decision

Add `cobra_core.security` as ISPF:

```
Identity → Authentication → Roles → Permissions → Policies → Authorization Engine
        → Cases / Workflows / ISF / KEF / Plugins / Operations / Evidence Vault
```

ISPF owns:

- Principal types (user, service, API client, plugin, workflow, system)
- Built-in + custom roles with additive permissions
- Deterministic policy evaluation (allow / deny / conditional)
- Central `authorize()` engine with audit references
- Session tracking + revocation (opaque tokens; no credential exposure)
- Least-privilege service identities
- Authenticated read APIs under `/security/*`

ISPF does **not** own SSO, OAuth, SAML, OIDC, LDAP, Active Directory, external IdPs, or production enablement.

## Consequences

- No implicit administrator bypass — admin permissions are an explicit role grant set
- Default deny when no allow policy/permission matches
- Subsystems should call `authorize()`; this milestone does not rewire existing routes
- Production remains disabled; no automatic merge
