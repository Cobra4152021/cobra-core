# Runbook

1. Set `COBRA_CORE_AUTH_SECRET` (non-default)
2. Keep `COBRA_CORE_PRODUCTION` / production flags **off**
3. `run_startup_validation()` — abort if critical
4. `MIGRATIONS.dry_run()` then apply pending if approved
5. `BACKUP.create()` before risky changes
6. `GET /production/health` → ready
7. `run_security_review()` → all ok
8. Load suite 100→500→1000
9. On failure: enter maintenance, restore dry-run, rollback migration, exit maintenance
