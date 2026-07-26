# Plugin Developer Guide

## Layout

```
my_plugin/
  plugin.json
  extension.py   # exposes register()
```

## Minimal skill example

`plugin.json`:

```json
{
  "plugin_id": "sample.my_skill",
  "name": "My Skill",
  "version": "1.0.0",
  "author": "You",
  "description": "Demo",
  "license": "UNLICENSED",
  "supported_core_version": "0.9.x",
  "plugin_type": "isf_skill",
  "entry_point": "cobra_core.plugins.samples.my_plugin.extension",
  "required_permissions": ["register_skill"],
  "dependencies": []
}
```

`extension.py`:

```python
def register():
    return {
        "extension_id": "sample.my_skill.v1",
        "skill_id": "my_skill",
        "title": "My Skill",
    }
```

## HTTP (authenticated)

- `GET /plugins`
- `GET /plugins/status`
- `GET /plugins/{id}`
- `POST /plugins/{id}/enable`
- `POST /plugins/{id}/disable`

No upload or remote install endpoints.

## Reference samples

- `sample.vehicle_skill`
- `sample.policy_report`
- `sample.budget_dataset`
- `sample.case_template`

These are demonstrations only and do not wire into production Core registries.
