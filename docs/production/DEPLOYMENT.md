# Deployment

Production enablement remains **disabled**.

Admin endpoints (Bearer, not PASF):

- `GET /production/status`
- `GET /production/health`
- `GET /production/diagnostics`
- `GET /production/startup-report`
- `GET /production/metrics`
- `GET /production/integrity`
- `GET /production/security-review`
- `GET /production/migrations/dry-run`
- `GET /production/audit`

Certification phases: local → offline staging → performance → security → recovery → migration → soak 24h → rollback.
