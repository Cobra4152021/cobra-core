import type { CkeStore } from "../db/store.js";
import { canRead } from "../permissions/index.js";
import type { AuthContext, Entity, Relationship } from "../types.js";
import { RelationshipEngine } from "../relationship/index.js";

export interface GraphNode {
  entity: Entity;
  depth: number;
}

export interface GraphTraverseResult {
  nodes: GraphNode[];
  edges: Relationship[];
}

export class KnowledgeGraph {
  private rels: RelationshipEngine;

  constructor(private store: CkeStore) {
    this.rels = new RelationshipEngine(store);
  }

  outgoing(ctx: AuthContext, entityId: string, minConfidence = 0): Relationship[] {
    return this.rels
      .list(ctx)
      .filter((r) => r.fromEntityId === entityId && r.confidence >= minConfidence);
  }

  incoming(ctx: AuthContext, entityId: string, minConfidence = 0): Relationship[] {
    return this.rels
      .list(ctx)
      .filter((r) => r.toEntityId === entityId && r.confidence >= minConfidence);
  }

  traverse(
    ctx: AuthContext,
    startId: string,
    opts: {
      maxDepth?: number;
      projectId?: string | null;
      minConfidence?: number;
      direction?: "out" | "in" | "both";
    } = {},
  ): GraphTraverseResult {
    const maxDepth = opts.maxDepth ?? 2;
    const minC = opts.minConfidence ?? 0;
    const dir = opts.direction ?? "both";
    const visited = new Set<string>();
    const nodes: GraphNode[] = [];
    const edges: Relationship[] = [];
    const queue: Array<{ id: string; depth: number }> = [{ id: startId, depth: 0 }];

    while (queue.length) {
      const cur = queue.shift()!;
      if (visited.has(cur.id)) continue;
      visited.add(cur.id);
      const ent = this.store.entities.get(cur.id);
      if (!ent || ent.orgId !== ctx.orgId) continue;
      if (!canRead(ctx, ent.permissions)) continue;
      if (opts.projectId != null && ent.projectId != null && ent.projectId !== opts.projectId) {
        continue;
      }
      nodes.push({ entity: ent, depth: cur.depth });
      if (cur.depth >= maxDepth) continue;

      const nextRels: Relationship[] = [];
      if (dir === "out" || dir === "both") nextRels.push(...this.outgoing(ctx, cur.id, minC));
      if (dir === "in" || dir === "both") nextRels.push(...this.incoming(ctx, cur.id, minC));
      for (const r of nextRels) {
        if (opts.projectId != null && r.projectId != null && r.projectId !== opts.projectId) continue;
        if (!canRead(ctx, r.permissions)) continue;
        edges.push(r);
        const nid = r.fromEntityId === cur.id ? r.toEntityId : r.fromEntityId;
        if (!visited.has(nid)) queue.push({ id: nid, depth: cur.depth + 1 });
      }
    }
    return { nodes, edges };
  }
}
