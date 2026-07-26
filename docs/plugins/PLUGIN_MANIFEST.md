# Plugin Manifest

Each plugin ships a `plugin.json` beside its entry module.

## Required fields

| Field | Description |
|-------|-------------|
| `plugin_id` | Stable unique id (not under reserved namespaces) |
| `name` | Display name |
| `version` | Plugin semver |
| `author` | Author string |
| `description` | Short description |
| `license` | License identifier |
| `supported_core_version` | e.g. `0.9.x` or exact semver |
| `plugin_type` | Registry type (see PLUGIN_TYPES.md) |
| `entry_point` | Import path under allowed prefixes |
| `required_permissions` | Non-empty permission list |

## Optional fields

| Field | Description |
|-------|-------------|
| `dependencies` | Other `plugin_id` values that must be present |
| `checksum` | SHA-256 of manifest (+ entry file when verified) |
| `signature` | Reserved for future signing |
| `min_core_version` / `max_core_version` | Compatibility bounds |
| `required_apis` | PEF APIs (`pef.extension_v1`, `pef.manifest_v1`) |
| `schema_version` | Manifest schema version (default `1`) |

## Entry contract

The entry module must expose:

```python
def register() -> dict | list[dict]:
    ...
```

Return values are stored as extension payloads. Keys `mutate_core`, `patch_core`, and `monkeypatch` are stripped.
