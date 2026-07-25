# ADR-0003 — Investigation Skills Framework (ISF)

**Status:** Accepted (KC-024)  
**Date:** 2026-07-25  
**Depends on:** KC-022 AIR, KC-023 AIR staging cert  
**Does not modify:** Protocol V1 wire; prior certification tags

## Context

Computer previously approached Core with capability lists (or profiles that expand to them). Investigation workflows need a higher-level, auditable contract: named skills with evidence requirements, structured outputs, and confidence gates — while AIR remains responsible for provider/model selection.

## Decision

Introduce **ISF**:

1. Computer requests an **investigation skill** (`skill_id` + evidence refs).
2. Skill Engine loads a **manifest** from the **registry**.
3. Manifest expands to required capabilities, evidence checks, and output schema.
4. AIR routes using expanded capabilities.
5. Results are **typed structured objects** with confidence disposition.
6. Missing required evidence fails closed with `missing_required_evidence`.
7. Confidence below the skill threshold forces `needs_human_review`.

## Consequences

- New package: `cobra_core.isf`
- Ten built-in skills registered at import
- Future skills: register a manifest + schema only (no engine rewrite)
- No autonomous actions, marketplace, or production enablement in this ADR
