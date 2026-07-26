# Tenancy

Every resource belongs to exactly one organization.

Default: **cross-organization access denied**.

`TenantContext` includes:

- `organization_id`
- `department_id`
- `principal_id`
- `membership_roles`
- `policy_version`

Resolve via `TENANCY.resolve_context(principal_id, organization_id, department_id=...)`.
