# Organization Model

| Field | Description |
|-------|-------------|
| `organization_id` | Stable unique id |
| `name` | Display name |
| `status` | `active` \| `suspended` \| `archived` |
| `classification` | Data classification |
| `created` | Unix timestamp |
| `owner` | Principal id of organization owner |
| `configuration` | Feature flags, quotas, plugin/workflow/benchmark availability, policy overrides |
| `security_policies` | Org policy document (no secrets) |
| `quota` | Operational limits |
| `branding` | Reserved (not exposed) |
