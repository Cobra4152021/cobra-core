import type { CkeStore } from "../db/store.js";
import { filterReadable, projectScopedOrThrow } from "../permissions/index.js";
import type { AuthContext, CitationRef, Relationship, Visibility } from "../types.js";
import { clampConfidence, newId, now } from "../util.js";

export const REL_TYPES = [
  "contains",
  "works_on",
  "references",
  "depends_on",
  "occurred_before",
  "decided",
  "related_to",
] as const;

export class RelationshipEngine {
  constructor(private store: CkeStore) {}

  create(
    ctx: AuthContext,
    input: {
      fromEntityId: string;
      toEntityId: string;
      relType: string;
      projectId?: string | null;
      confidence?: number;
      evidence?: string[];
      citations?: CitationRef[];
      visibility?: Visibility;
    },
  ): Relationship {
    projectScopedOrThrow(ctx, input.projectId);
    const from = this.store.entities.get(input.fromEntityId);
    const to = this.store.entities.get(input.toEntityId);
    if (!from || !to || from.orgId !== ctx.orgId || to.orgId !== ctx.orgId) {
      throw new Error("Entities not found in org");
    }
    const existing = [...this.store.relationships.values()].find(
      (r) =>
        r.orgId === ctx.orgId &&
        r.fromEntityId === input.fromEntityId &&
        r.toEntityId === input.toEntityId &&
        r.relType === input.relType,
    );
    if (existing) {
      existing.confidence = Math.max(existing.confidence, clampConfidence(input.confidence ?? 0.5));
      existing.evidence = Array.from(new Set([...existing.evidence, ...(input.evidence ?? [])]));
      existing.updatedAt = now();
      return existing;
    }
    const ts = now();
    const rel: Relationship = {
      id: newId("rel"),
      orgId: ctx.orgId,
      projectId: input.projectId ?? null,
      fromEntityId: input.fromEntityId,
      toEntityId: input.toEntityId,
      relType: input.relType,
      confidence: clampConfidence(input.confidence ?? 0.6),
      evidence: input.evidence ?? [],
      citations: input.citations ?? [],
      permissions: {
        orgId: ctx.orgId,
        projectId: input.projectId ?? null,
        ownerUserId: ctx.userId,
        visibility: input.visibility ?? "project",
      },
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.relationships.set(rel.id, rel);
    return rel;
  }

  list(ctx: AuthContext, opts: { projectId?: string | null } = {}): Relationship[] {
    const rows = [...this.store.relationships.values()].filter((r) => {
      if (r.orgId !== ctx.orgId) return false;
      if (opts.projectId != null && r.projectId !== opts.projectId) return false;
      return true;
    });
    return filterReadable(ctx, rows);
  }

  /** Heuristic: link project entity to mentioned document/tech entities. */
  inferFromEntities(ctx: AuthContext, entities: { id: string; type: string }[], projectId?: string | null): Relationship[] {
    const projectEnt = entities.find((e) => e.type === "project");
    const out: Relationship[] = [];
    if (!projectEnt) return out;
    for (const e of entities) {
      if (e.id === projectEnt.id) continue;
      if (e.type === "document") {
        out.push(
          this.create(ctx, {
            fromEntityId: projectEnt.id,
            toEntityId: e.id,
            relType: "contains",
            projectId,
            evidence: ["inferred: project contains document"],
          }),
        );
      } else if (e.type === "person") {
        out.push(
          this.create(ctx, {
            fromEntityId: e.id,
            toEntityId: projectEnt.id,
            relType: "works_on",
            projectId,
            evidence: ["inferred: person works_on project"],
          }),
        );
      } else if (e.type === "technology" || e.type === "product") {
        out.push(
          this.create(ctx, {
            fromEntityId: projectEnt.id,
            toEntityId: e.id,
            relType: "depends_on",
            projectId,
            evidence: ["inferred: project depends_on technology"],
          }),
        );
      }
    }
    return out;
  }
}
