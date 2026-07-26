# ADR-0011 — Plugin & Extension Framework (PEF)

## Status

Accepted (KC-033)

## Context

Cobra Core ships AIR, ISF, KEF, RRF, Evidence Vault connectivity, Workflow/Case surfaces, Benchmark, and Operations Control Plane. Extensions must be possible without modifying Core objects, without remote code download, and without runtime code generation.

## Decision

Add `cobra_core.plugins` as a declarative Plugin & Extension Framework:

```
Administrator → Plugin Registry → Plugin Loader → Plugin Manager → Extension Points → Core
```

PEF owns:

- Manifest-driven plugin discovery (local packages only)
- Fail-closed validation (permissions, compatibility, checksum, namespaces)
- Lifecycle: discover → validate → load → enable / disable → unload / reload
- Extension registration into an isolated PEF registry (never mutates Core)
- Authenticated HTTP under `/plugins/*` (list, status, get, enable, disable)
- Audit + metrics for load/enable/disable/validation/permission events

PEF does **not** own marketplace, remote install, upload endpoints, executable scripts, sandboxed runtimes, or production enablement.

## Consequences

- Sample plugins demonstrate types without wiring into SKILL_REGISTRY / KEF connectors
- Future plugin types are registry-based (`PluginType` + `TYPE_PERMISSIONS`)
- Staging may hot-reload local packages; production remains disabled
- No automatic merge
