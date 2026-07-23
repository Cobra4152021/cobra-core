# KC-003 — Timeline

Events are stored with `occurred_at` and listed in ascending chronological order.

Supports:

- project timeline  
- organization timeline (filter by org)  
- entity timeline (`entityId`)  
- decision / investigation history via `eventType`

Document revisions can be recorded as `eventType: document_revision` with citations pointing to document hashes.
