# Authorization

All protected subsystems should call the same engine:

```python
from cobra_core.security import authorize, ResourceRef, ResourceType

decision = authorize(
    principal_id="user_inv",
    action="run_workflow",
    resource_type=ResourceType.WORKFLOW,
    resource_id="wf_1",
)
if decision.allowed():
    ...
```

## Decision fields

- `effect` — allow | deny | conditional
- `reason`
- `policy_id`
- `audit_ref`
- `principal_id`, `action`, `resource_type`
- `required_permission`
- `conditions`

`require()` raises `SecurityError` unless effect is `allow`.

KC-034 introduces the engine; it does not change AIR/ISF/KEF routing or AI behavior.
