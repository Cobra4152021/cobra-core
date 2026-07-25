# Skill Registry

## Purpose

Skills **register themselves**. Computer never hardcodes skill definitions — it only references `skill_id`.

## API

```python
from cobra_core.isf import SKILL_REGISTRY, SkillManifest, register_builtin_skills

register_builtin_skills()  # idempotent for builtins
manifest = SKILL_REGISTRY.get("vehicle_damage_assessment")
for skill in SKILL_REGISTRY.list_skills():
    ...
```

## Adding a future skill

1. Add a Pydantic output model in `isf/schemas.py` and map it in `SCHEMA_BY_SKILL_ID`.
2. Construct a `SkillManifest` with capabilities + evidence types.
3. `registry.register(manifest)`.

No `SkillEngine` modifications required for registration-only additions.
