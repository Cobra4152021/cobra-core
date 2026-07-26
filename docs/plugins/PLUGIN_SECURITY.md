# Plugin Security

## Hard rules

- No remote plugin marketplace
- No automatic downloads
- No upload HTTP endpoint
- No runtime code generation
- No dynamic code execution outside `importlib.import_module` of allow-listed entry points
- Fail closed on validation, permission, and compatibility errors

## Controls

1. **Entry prefix allow-list** — default `cobra_core.plugins.samples.`
2. **Reserved namespaces** — `cobra.`, `core.`, `system.` blocked for plugin ids
3. **Explicit permissions** — type requires matching permission; unknown permissions denied
4. **Checksum** — when declared, must match computed SHA-256
5. **Signature** — field reserved; not yet enforced
6. **Isolated registry** — extensions never mutate Core registries/objects
7. **Audit** — load, enable, disable, validation failure, compatibility failure, permission denial

## Staging vs production

- Staging/dev: local hot-load allowed (`PEF_HOT_LOAD`)
- Production: PEF and Core production enablement remain disabled for this milestone
