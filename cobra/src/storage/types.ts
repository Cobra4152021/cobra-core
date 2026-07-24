/**
 * Storage-independent interfaces for CKE (KC-003A).
 * In-memory adapter for tests; D1 adapter lives in Cobra Computer Worker.
 */

export type OrgScoped = { orgId: string; projectId?: string | null };

export interface CkeStorageAdapter {
  listProjects(orgId: string): Promise<unknown[]>;
  getProject(orgId: string, projectId: string): Promise<unknown | null>;
  insertProject(row: OrgScoped & { name: string; slug: string; ownerUserId: string }): Promise<unknown>;

  listMemories(orgId: string, opts?: { projectId?: string | null; type?: string }): Promise<unknown[]>;
  insertMemory(row: OrgScoped & Record<string, unknown>): Promise<unknown>;

  listEntities(orgId: string, projectId?: string | null): Promise<unknown[]>;
  upsertEntity(row: OrgScoped & Record<string, unknown>): Promise<unknown>;

  listRelationships(orgId: string, projectId?: string | null): Promise<unknown[]>;
  insertRelationship(row: OrgScoped & Record<string, unknown>): Promise<unknown>;

  hybridSearch(orgId: string, q: string, opts?: { projectId?: string | null; limit?: number }): Promise<unknown[]>;
  getCitation(orgId: string, citationId: string): Promise<unknown | null>;
  insertCitation(row: OrgScoped & Record<string, unknown>): Promise<unknown>;

  /** Multi-record ops should run inside a transaction when the backend supports it. */
  withTransaction?<T>(fn: () => Promise<T>): Promise<T>;
}
