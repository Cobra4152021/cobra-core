# KC-003 — Graph Schema

## Entities

Types: person, organization, project, location, product, event, date, document, technology, other.

Fields: stable UUID, aliases, description, type, created/updated, confidence, ACL.

## Relationships

Examples: `contains`, `works_on`, `references`, `depends_on`, `occurred_before`, `decided`, `related_to`.

Fields: confidence, evidence[], citations[], created_at/updated_at, ACL.

## Traversal

`KnowledgeGraph.traverse` supports:

- incoming / outgoing / both
- max depth
- project filter
- confidence filter
- permission filtering on every node/edge

## Persistence

SQL tables: `cke_entities`, `cke_relationships`, `cke_graph_index` (see `cobra/migrations/001_cke_schema.sql`).
