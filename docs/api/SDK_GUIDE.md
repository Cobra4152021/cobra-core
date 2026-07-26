# SDK Guide

## Layout

```
src/cobra_core/api/sdk/
  python/cobra_sdk/     # reference Python client
  typescript/src/       # reference TypeScript client
  examples/             # create case, run workflow, evidence, report, orgs
```

## Features

- Bearer authentication (ISPF)
- `X-Cobra-Org-Id` / `X-Cobra-Principal-Id`
- `X-Cobra-Sdk-Version` for metrics
- Cursor pagination helpers
- Typed/structured `CobraApiError`

## Python

```python
from cobra_core.api.sdk.python.cobra_sdk import CobraClient
client = CobraClient(base_url, token=token, organization_id="org_x", principal_id="user_x")
```

## TypeScript

```ts
import { CobraClient } from "./client";
const client = new CobraClient({ baseUrl, token, organizationId: "org_x" });
```
