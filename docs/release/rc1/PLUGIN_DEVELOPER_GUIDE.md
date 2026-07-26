# Plugin Developer Guide — RC1

See also: `docs/plugins/PLUGIN_DEVELOPER_GUIDE.md`.

RC1 freeze:

- Manifest schema locked
- Entry points must stay under allow-listed prefixes (`cobra_core.plugins.samples.` by default)
- Permissions explicit; fail closed
- No remote install / upload / runtime codegen

Sample plugins: `sample.vehicle_skill`, `sample.policy_report`, `sample.budget_dataset`, `sample.case_template`.
