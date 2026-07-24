# KC-003 — API

Framework-agnostic handler: `CkeApi` in `cobra/src/api`.

## GET

| Path | Description |
|------|-------------|
| `/projects` | List accessible projects |
| `/projects/{id}` | Project detail |
| `/memory` | List memory (`projectId`, `type`) |
| `/entities` | List entities |
| `/relationships` | List relationships |
| `/graph` | Traverse (`entityId`, `depth`, `minConfidence`) |
| `/search` | Hybrid search (`q`, `projectId`) |
| `/timeline` | Chronology |
| `/metrics` | Observability snapshot |

## POST

| Path | Description |
|------|-------------|
| `/project` | Create project |
| `/memory` | Create memory |
| `/entity` | Upsert entity |
| `/relationship` | Create relationship |
| `/investigate` | Reasoning pipeline |
| `/decision` | Record decision |

## Streaming

`streamInvestigate` yields answer chunks then a `__META__` JSON trailer.

## Mounting (future)

Additive Worker route prefix `/api/cke/*` — **do not** alter chat/benchmark routes.
