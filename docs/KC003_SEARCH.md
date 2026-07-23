# KC-003 — Hybrid Search

Signals combined:

| Signal | Role |
|--------|------|
| Keyword | Primary lexical match |
| Knowledge graph | Neighbor expansion from seed entity |
| Recency | Time decay boost |
| Authority | Object confidence / importance |
| Permissions | Deny-by-default ACL |
| Project relevance | Same-project boost |
| Embeddings | **Optional** additive score only |

Search **must not** rely on embeddings alone (`SearchEngine.search`).
