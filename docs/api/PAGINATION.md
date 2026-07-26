# Pagination

Deterministic cursor pagination:

| Field | Meaning |
|-------|---------|
| `limit` | Page size (1–100, default 25) |
| `cursor` | Opaque offset cursor |
| `next_cursor` | Next page cursor or null |

Response shape:

```json
{
  "data": [],
  "pagination": { "limit": 25, "cursor": null, "next_cursor": "…" }
}
```
