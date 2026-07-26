# Security Checklist

Automated via `run_security_review()` / `GET /production/security-review`:

- [ ] Default-deny authorization (no admin bypass)
- [ ] No credential logging in audit channels
- [ ] Bearer validation present
- [ ] Plugin entry allow-list + reserved namespaces
- [ ] Cross-org isolation (`allow_cross_org=false`)
- [ ] OpenAPI requires authentication
- [ ] Debug disabled
- [ ] Production enablement disabled
