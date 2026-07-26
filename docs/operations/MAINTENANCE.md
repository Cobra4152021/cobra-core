# Maintenance Mode

## Enter

`MAINTENANCE.enter(actor=..., reason=..., drain_workflows=True, reject_new_workflows=True)`

Effects:

- Component health reports `maintenance`
- New workflows rejected when `reject_new_workflows=True`
- Metrics, audit, and reporting **continue**
- Investigation routing code is not rewritten; callers must honor `allow_new_workflow()` / `writes_allowed()`

## Exit

`MAINTENANCE.exit(actor=...)` clears maintenance state and audits `maintenance_exit`.

## Read-only mode

Independent flag `READ_ONLY_MODE`:

- Allowed: search, reports, metrics, audit, status APIs
- Denied: new cases, workflow execution, approvals, writes (via `writes_allowed()`)
