# Roles

## Built-in

| Role | Intent |
|------|--------|
| `administrator` | Full explicit permission set (no bypass flag) |
| `supervisor` | Broad case/workflow/ops oversight |
| `investigator` | Create cases, run workflows, retrieve evidence |
| `reviewer` | Approve workflows/findings |
| `observer` | View metrics/security only (no evidence retrieve) |
| `service` | Minimal service baseline |
| `plugin` | register_plugin |

## Custom roles

`ROLE_REGISTRY.register_custom(name, permissions)` adds additive custom roles.

Permissions from multiple roles are unioned (additive).
