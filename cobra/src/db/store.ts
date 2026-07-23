import type {
  Conflict,
  Decision,
  Entity,
  Fact,
  Memory,
  Project,
  Relationship,
  TimelineEvent,
  CitationRef,
} from "../types.js";

/** In-memory store mirroring CKE tables. Swap for D1 adapter later. */
export class CkeStore {
  projects = new Map<string, Project>();
  memories = new Map<string, Memory>();
  entities = new Map<string, Entity>();
  relationships = new Map<string, Relationship>();
  facts = new Map<string, Fact>();
  citations = new Map<string, CitationRef & { orgId: string; projectId?: string | null; createdAt: number }>();
  timeline = new Map<string, TimelineEvent>();
  decisions = new Map<string, Decision>();
  conflicts = new Map<string, Conflict>();
  searchIndex: Array<{
    id: string;
    orgId: string;
    projectId?: string | null;
    objectType: string;
    objectId: string;
    text: string;
    keywords: string;
    authority: number;
    recency: number;
    visibility: string;
    ownerUserId?: string | null;
  }> = [];

  clear(): void {
    this.projects.clear();
    this.memories.clear();
    this.entities.clear();
    this.relationships.clear();
    this.facts.clear();
    this.citations.clear();
    this.timeline.clear();
    this.decisions.clear();
    this.conflicts.clear();
    this.searchIndex = [];
  }
}

export type DbLike = CkeStore;
