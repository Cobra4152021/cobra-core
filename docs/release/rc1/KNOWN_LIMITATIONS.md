# Known Limitations — RC1

1. **24-hour staging soak** not completed in the offline certification pack (blocking for RC approval).
2. **Tag collision:** repository already had `v1.0.0-rc1` (KC-011). KC-038 tagged `v1.0.0-rc1.kc038` on the certification commit without force-moving the legacy tag.
3. Production enablement hard-disabled.
3. Workflow/case engines are framework-scoped (not full durable case products).
4. Migrations are metadata framework-only (no external DB engine).
5. Vault live connectivity depends on staging network/Bot Fight Mode controls.
6. Webhooks reserved (no delivery).
7. No SSO/OIDC/SAML/federation.
8. SDKs are reference clients (Python/TypeScript), not separately versioned packages on a registry.
