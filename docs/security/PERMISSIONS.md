# Permissions

Permissions are additive. Unknown permissions fail closed.

## Built-in

- `create_case`, `close_case`
- `run_workflow`, `approve_workflow`, `approve_findings`
- `retrieve_evidence`
- `register_plugin`, `manage_plugins`
- `run_benchmark`
- `view_metrics`, `view_audit`, `view_security`
- `manage_operations`, `manage_users`, `manage_roles`, `manage_policies`

Actions map to permissions via `ACTION_PERMISSIONS` in `schemas.py`.

There is **no** implicit administrator bypass.
