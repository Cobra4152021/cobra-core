# Deployment Guide — RC1

1. Deploy **staging only** (production disabled).
2. Set `COBRA_CORE_AUTH_SECRET` (strong, non-default).
3. Keep `COBRA_CORE_PRODUCTION` / production flags **off**.
4. Run startup validation: `run_startup_validation()` or `GET /production/startup-report`.
5. Migrations dry-run: `GET /production/migrations/dry-run`.
6. Smoke: `GET /api/v1/status`, `GET /api/v1/openapi.json` (Bearer).
7. Security review: `GET /production/security-review`.
8. Begin 24-hour staging soak; collect memory/latency/errors/audit.

Do not enable production until soak + rollback phases are signed off.
