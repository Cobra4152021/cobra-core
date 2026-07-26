# Isolation

## Resource tagging (immutable)

- `organization_id`
- `department_id`
- `resource_owner`
- `classification`
- `creation_time`

Mutation of ownership is rejected (`ownership_immutable`), except administrative **case move**.

## Case move

Requires:

1. Organization owner/administrator membership in source and destination
2. Authorization decision
3. Audit entry

## Scopes

| Asset | Scopes |
|-------|--------|
| Plugins | global / organization / department |
| Benchmarks | global / organization / private |
| Workflows | per-org availability map |
| Cases | single organization |
