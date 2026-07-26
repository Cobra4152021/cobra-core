# Restore

1. Load backup JSON
2. Validate compatibility (`format`, no vault bodies, required blocks)
3. Dry-run optional
4. Non-destructive org metadata merge when applying

Reject incompatible backups fail-closed.
