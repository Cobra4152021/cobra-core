-- Cobra Knowledge Engine (KC-003)
-- D1 / SQLite compatible. Additive tables only — do not alter chat/benchmark tables.

CREATE TABLE IF NOT EXISTS cke_projects (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  name TEXT NOT NULL,
  slug TEXT NOT NULL,
  description TEXT,
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'private',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE(org_id, slug)
);
CREATE INDEX IF NOT EXISTS idx_cke_projects_org ON cke_projects(org_id);

CREATE TABLE IF NOT EXISTS cke_memories (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  type TEXT NOT NULL,
  content TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.5,
  source TEXT NOT NULL,
  citations_json TEXT NOT NULL DEFAULT '[]',
  permissions_json TEXT NOT NULL DEFAULT '{}',
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  content_hash TEXT NOT NULL,
  expires_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_memories_org_project ON cke_memories(org_id, project_id);
CREATE INDEX IF NOT EXISTS idx_cke_memories_type ON cke_memories(type);
CREATE INDEX IF NOT EXISTS idx_cke_memories_hash ON cke_memories(content_hash);

CREATE TABLE IF NOT EXISTS cke_entities (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  type TEXT NOT NULL,
  canonical_name TEXT NOT NULL,
  aliases_json TEXT NOT NULL DEFAULT '[]',
  description TEXT,
  confidence REAL NOT NULL DEFAULT 0.5,
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_entities_org_type ON cke_entities(org_id, type);
CREATE INDEX IF NOT EXISTS idx_cke_entities_name ON cke_entities(org_id, canonical_name);

CREATE TABLE IF NOT EXISTS cke_relationships (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  from_entity_id TEXT NOT NULL,
  to_entity_id TEXT NOT NULL,
  rel_type TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.5,
  evidence_json TEXT NOT NULL DEFAULT '[]',
  citations_json TEXT NOT NULL DEFAULT '[]',
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_rel_from ON cke_relationships(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_cke_rel_to ON cke_relationships(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_cke_rel_type ON cke_relationships(org_id, rel_type);

CREATE TABLE IF NOT EXISTS cke_facts (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  statement TEXT NOT NULL,
  confidence REAL NOT NULL DEFAULT 0.5,
  entity_ids_json TEXT NOT NULL DEFAULT '[]',
  citations_json TEXT NOT NULL DEFAULT '[]',
  content_hash TEXT NOT NULL,
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_facts_org_project ON cke_facts(org_id, project_id);
CREATE INDEX IF NOT EXISTS idx_cke_facts_hash ON cke_facts(content_hash);

CREATE TABLE IF NOT EXISTS cke_citations (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  evidence_kind TEXT NOT NULL,
  document_id TEXT,
  document_hash TEXT,
  page INTEGER,
  line_start INTEGER,
  line_end INTEGER,
  uri TEXT,
  excerpt TEXT,
  confidence REAL NOT NULL DEFAULT 1.0,
  immutable INTEGER NOT NULL DEFAULT 1,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_citations_doc ON cke_citations(document_id);

CREATE TABLE IF NOT EXISTS cke_timeline (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  entity_id TEXT,
  event_type TEXT NOT NULL,
  title TEXT NOT NULL,
  body TEXT,
  occurred_at INTEGER NOT NULL,
  citations_json TEXT NOT NULL DEFAULT '[]',
  confidence REAL NOT NULL DEFAULT 0.5,
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_timeline_org_time ON cke_timeline(org_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_cke_timeline_project ON cke_timeline(project_id, occurred_at);

CREATE TABLE IF NOT EXISTS cke_decisions (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  title TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT,
  alternatives_json TEXT NOT NULL DEFAULT '[]',
  decision_maker TEXT,
  evidence_json TEXT NOT NULL DEFAULT '[]',
  citations_json TEXT NOT NULL DEFAULT '[]',
  decided_at INTEGER NOT NULL,
  owner_user_id TEXT,
  visibility TEXT NOT NULL DEFAULT 'project',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_decisions_project ON cke_decisions(project_id);

CREATE TABLE IF NOT EXISTS cke_conflicts (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  conflict_type TEXT NOT NULL,
  summary TEXT NOT NULL,
  left_ref TEXT NOT NULL,
  right_ref TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  details_json TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_conflicts_status ON cke_conflicts(org_id, status);

CREATE TABLE IF NOT EXISTS cke_search_index (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  text TEXT NOT NULL,
  keywords TEXT NOT NULL,
  authority REAL NOT NULL DEFAULT 0.5,
  recency INTEGER NOT NULL,
  visibility TEXT NOT NULL DEFAULT 'project',
  owner_user_id TEXT,
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_search_org ON cke_search_index(org_id);
CREATE INDEX IF NOT EXISTS idx_cke_search_kw ON cke_search_index(org_id, keywords);

CREATE TABLE IF NOT EXISTS cke_graph_index (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  project_id TEXT,
  entity_id TEXT NOT NULL,
  neighbor_id TEXT NOT NULL,
  rel_type TEXT NOT NULL,
  direction TEXT NOT NULL,
  confidence REAL NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cke_graph_entity ON cke_graph_index(entity_id, direction);
