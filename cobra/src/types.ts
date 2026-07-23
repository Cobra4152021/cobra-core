/** Shared CKE domain types (KC-003). */

export type MemoryType =
  | "session"
  | "project"
  | "organization"
  | "research"
  | "long_term"
  | "user";

export type EntityType =
  | "person"
  | "organization"
  | "project"
  | "location"
  | "product"
  | "event"
  | "date"
  | "document"
  | "technology"
  | "other";

export type Visibility = "private" | "project" | "organization" | "public";

export type DecisionStatus = "proposed" | "approved" | "rejected" | "superseded";

export type ConflictType =
  | "contradictory_facts"
  | "duplicate_entities"
  | "version_conflict"
  | "document_conflict"
  | "timeline_conflict"
  | "confidence_conflict";

export interface Acl {
  orgId: string;
  projectId?: string | null;
  ownerUserId?: string | null;
  visibility: Visibility;
  /** Explicit allow-list of user ids (optional). */
  allowUserIds?: string[];
}

export interface CitationRef {
  id: string;
  evidenceKind: string;
  documentId?: string | null;
  documentHash?: string | null;
  page?: number | null;
  lineStart?: number | null;
  lineEnd?: number | null;
  uri?: string | null;
  excerpt?: string | null;
  confidence: number;
}

export interface Project {
  id: string;
  orgId: string;
  name: string;
  slug: string;
  description?: string | null;
  ownerUserId?: string | null;
  visibility: Visibility;
  createdAt: number;
  updatedAt: number;
}

export interface Memory {
  id: string;
  orgId: string;
  projectId?: string | null;
  type: MemoryType;
  content: string;
  confidence: number;
  source: string;
  citations: CitationRef[];
  permissions: Acl;
  contentHash: string;
  expiresAt?: number | null;
  createdAt: number;
  updatedAt: number;
}

export interface Entity {
  id: string;
  orgId: string;
  projectId?: string | null;
  type: EntityType;
  canonicalName: string;
  aliases: string[];
  description?: string | null;
  confidence: number;
  permissions: Acl;
  createdAt: number;
  updatedAt: number;
}

export interface Relationship {
  id: string;
  orgId: string;
  projectId?: string | null;
  fromEntityId: string;
  toEntityId: string;
  relType: string;
  confidence: number;
  evidence: string[];
  citations: CitationRef[];
  permissions: Acl;
  createdAt: number;
  updatedAt: number;
}

export interface Fact {
  id: string;
  orgId: string;
  projectId?: string | null;
  statement: string;
  confidence: number;
  entityIds: string[];
  citations: CitationRef[];
  contentHash: string;
  permissions: Acl;
  createdAt: number;
  updatedAt: number;
}

export interface TimelineEvent {
  id: string;
  orgId: string;
  projectId?: string | null;
  entityId?: string | null;
  eventType: string;
  title: string;
  body?: string | null;
  occurredAt: number;
  citations: CitationRef[];
  confidence: number;
  permissions: Acl;
  createdAt: number;
}

export interface Decision {
  id: string;
  orgId: string;
  projectId?: string | null;
  title: string;
  status: DecisionStatus;
  reason?: string | null;
  alternatives: string[];
  decisionMaker?: string | null;
  evidence: string[];
  citations: CitationRef[];
  decidedAt: number;
  permissions: Acl;
  createdAt: number;
  updatedAt: number;
}

export interface Conflict {
  id: string;
  orgId: string;
  projectId?: string | null;
  conflictType: ConflictType;
  summary: string;
  leftRef: string;
  rightRef: string;
  status: "open" | "resolved" | "ignored";
  details: Record<string, unknown>;
  createdAt: number;
  updatedAt: number;
}

export interface AuthContext {
  orgId: string;
  userId: string;
  /** Projects the user may access. Empty = none. */
  projectIds: string[];
  /** Org-wide admin bypass for org-visibility objects. */
  isOrgAdmin?: boolean;
}

export interface SearchHit {
  objectType: string;
  objectId: string;
  score: number;
  snippet: string;
  projectId?: string | null;
  reasons: string[];
}

export interface InvestigateRequest {
  question: string;
  projectId?: string | null;
  maxDepth?: number;
  minConfidence?: number;
}

export interface InvestigateResult {
  answer: string;
  projectId?: string | null;
  memoriesUsed: string[];
  entitiesUsed: string[];
  factsUsed: string[];
  citations: CitationRef[];
  conflicts: Conflict[];
  decisions: Decision[];
  searchHits: SearchHit[];
  newKnowledgeStored: string[];
  metrics: Record<string, number>;
}
