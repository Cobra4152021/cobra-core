# OpenAPI

- Spec: OpenAPI **3.1**
- Endpoint: `GET /api/v1/openapi.json`
- Generation: deterministic (`json.dumps(..., sort_keys=True)`)
- Machine-readable JSON; human-readable via any OpenAPI viewer

Build programmatically:

```python
from cobra_core.api.openapi import build_openapi_document, render_openapi_json
```
