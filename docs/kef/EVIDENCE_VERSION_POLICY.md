# Evidence Version Policy

Modes: `latest` (default), `specific`, `effective_at`, `all`.

- Do not silently mix versions of the same `vault_document_id`
- Compliance reviews should supply `event_date` when effective-at selection is required
- Without event date, latest/current is used and recorded as `version_assumption`
