# KC-003 — Memory Model

## Types

| Type | Scope | Typical TTL |
|------|-------|-------------|
| `session` | Current conversation | Short / expirabl |
| `project` | One project | Durable |
| `organization` | Shared org knowledge | Durable |
| `research` | Discoveries / investigations | Durable |
| `long_term` | Hardened facts | Durable |
| `user` | Preferences, style, goals | Durable |

## Required fields

`id`, `type`, `created_at`, `updated_at`, `confidence`, `source`, `citations`, `permissions`, `project_id`, `hash` (`contentHash`).

## Rules

- Session memory is eligible for automatic expiry (`MemoryEngine.expireTemporary`).
- Project memory is ACL-scoped; no cross-project reads.
- Every write records `contentHash` for dedupe / conflict hooks.
