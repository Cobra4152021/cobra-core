# Runbook — RC1

## Incident: auth failures

1. Verify Bearer secret matches Core.
2. Confirm kill switch / `COBRA_CORE_ENABLED`.
3. Check `/production/diagnostics`.

## Incident: cross-org suspicion

1. Confirm MOTF `allow_cross_org=false`.
2. Review ISPF authorization audit for `cross_org_denied`.
3. Do not relax isolation.

## Incident: Vault unavailable

1. Expect KEF/evidence degradation.
2. Keep Core status/API health up.
3. Do not attempt vault object restore from Core backups.

## Rollback

1. Enter maintenance.
2. Restore last good backup (dry-run → apply).
3. Migration rollback if needed.
4. Exit maintenance; re-run startup validation.
