# Backup

Framework captures:

- Configuration metadata (secrets excluded)
- Organization metadata
- Case metadata indexes
- Evidence **references only** (no Vault object bodies)
- Recent audit excerpts
- Integrity checksums

Format: `prhf_backup_v1`. Artifacts written under `PRHF_BACKUP_ROOT` or `.prhf_backups/`.
