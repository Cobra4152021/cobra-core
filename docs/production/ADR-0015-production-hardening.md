# ADR-0015 — Production Readiness & Hardening Framework (PRHF)

## Status

Accepted (KC-037)

## Context

Cobra Core now includes AIR, ISF, KEF, RRF, Vault connectivity, Benchmark, Operations, PEF, ISPF, MOTF, and PASF. Enterprise readiness requires startup validation, migrations, backup/restore frameworks, expanded health, observability, performance sampling, integrity checks, and certification phases — without new investigation features or API/routing changes.

## Decision

Add `cobra_core.production` as PRHF:

```
Administrator → Operations → Deployment → Monitoring → Recovery → Cobra Core
```

PRHF owns startup validation, configuration checks, migration framework (dry-run), backup/restore frameworks, health expansion, diagnostics, integrity, performance sampling, load harness, security review automation, and certification phase scaffolding.

PRHF does **not** enable production, auto-scaling, Kubernetes, billing, or commercial licensing.

## Consequences

- Critical startup failures can abort when `PRHF_ABORT_ON_CRITICAL=true`
- Production enablement remains hard-disabled
- No changes to `/api/v1` contracts, AI routing, or workflows
