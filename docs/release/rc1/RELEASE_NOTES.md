# Cobra Core v1.0.0-rc1 — Release Notes

**Status:** Release Candidate (feature freeze)  
**Tag:** `v1.0.0-rc1`  
**Production:** disabled  

## Summary

RC1 certifies the King Cobra platform stack through KC-037 under a hard feature freeze. No new investigation features, APIs, or plugins are introduced in KC-038.

## Included platform (KC-021 → KC-037)

- Provider certification / CIAL
- AIR (+ certification)
- ISF (+ certification)
- RRF
- KEF + Evidence Vault connectivity
- Benchmark framework
- Operations Control Plane
- Plugin & Extension Framework
- Identity, Security & Policy (ISPF)
- Multi-Organization & Tenancy (MOTF)
- Public API & SDK (PASF `/api/v1`)
- Production Readiness & Hardening (PRHF)

## Freeze

Locked: Protocol V1, Public API v1, plugin manifests, org/security/workflow/case/benchmark/evidence schemas. Compatibility fixes only.

## Not in this RC

- Production enablement
- 24-hour staging soak completion (blocking for final approval)
- Federation, SSO, GraphQL/gRPC, webhook delivery
