import type { KnowledgeEngine } from "../knowledge/index.js";
import type { AuthContext } from "../types.js";

export interface JobResult {
  extractedEntities: number;
  relationships: number;
  expiredMemories: number;
  conflictsOpened: number;
  indexed: number;
}

/** Background maintenance — call from cron / queue later. */
export class BackgroundJobs {
  constructor(private ke: KnowledgeEngine) {}

  runMaintenance(ctx: AuthContext, projectId?: string | null): JobResult {
    let extracted = 0;
    let relationships = 0;
    let indexed = 0;

    // Re-extract from project memories lacking fresh graph links
    const memories = this.ke.memory.list(ctx, { projectId, type: "research" });
    for (const m of memories.slice(0, 50)) {
      const ents = this.ke.entities.extractFromText(ctx, m.content, projectId ?? m.projectId);
      extracted += ents.length;
      const rels = this.ke.relationships.inferFromEntities(
        ctx,
        ents.map((e) => ({ id: e.id, type: e.type })),
        projectId ?? m.projectId,
      );
      relationships += rels.length;
      this.ke.search.indexObject({
        orgId: ctx.orgId,
        projectId: m.projectId,
        objectType: "memory",
        objectId: m.id,
        text: m.content,
        authority: m.confidence,
        visibility: m.permissions.visibility,
        ownerUserId: m.permissions.ownerUserId,
      });
      indexed++;
    }

    const expiredMemories = this.ke.memory.expireTemporary(ctx);
    const conflicts = this.ke.conflicts.detectFactConflicts(ctx, projectId);

    // Confidence refresh: boost entities with many relationships
    for (const e of this.ke.entities.list(ctx, { projectId })) {
      const deg =
        this.ke.graph.outgoing(ctx, e.id).length + this.ke.graph.incoming(ctx, e.id).length;
      if (deg >= 3) e.confidence = Math.min(1, e.confidence + 0.05);
    }

    return {
      extractedEntities: extracted,
      relationships,
      expiredMemories,
      conflictsOpened: conflicts.length,
      indexed,
    };
  }
}
