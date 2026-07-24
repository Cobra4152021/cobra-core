# KC-012 — Sentinel Core (`sentinel-core-v0.1.0-alpha1`)

Pure TypeScript models for Cobra Sentinel:

- Correlation / bug / replay IDs
- Redaction helpers (secrets, cookies, evidence keys)
- Rule-based triage (never auto-close)
- Feedback workflow transitions
- Replay token builders (hashes only)

Exported from `@cobra-core/knowledge-engine` via `cobra/src/sentinel`.

Tests: `cobra/tests/sentinel.test.ts` (included in full suite, 89/89).
