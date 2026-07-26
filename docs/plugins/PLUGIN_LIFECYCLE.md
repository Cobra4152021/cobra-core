# Plugin Lifecycle

```
discover → validate → load → enable
                          ↘ disable → unload
load → reload (staging hot-load only)
```

| Action | Effect |
|--------|--------|
| `discover` | Read local `plugin.json` files into registry as `discovered` |
| `validate` | Manifest, permissions, compatibility, deps, checksum |
| `load` | Validate + import entry module + register extension payloads |
| `enable` | Mark loaded plugin active for PEF consumers |
| `disable` | Mark inactive; extensions remain registered until unload |
| `unload` | Disable (if needed) and remove from registry |
| `reload` | Unload + re-discover path + load (+ re-enable if previously enabled) |

Plugins never modify Core objects directly. Consumers read extension payloads from the PEF registry.
