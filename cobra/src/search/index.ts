import type { CkeStore } from "../db/store.js";
import { canRead } from "../permissions/index.js";
import type { AuthContext, SearchHit } from "../types.js";
import { newId, now } from "../util.js";
import { KnowledgeGraph } from "../graph/index.js";

function tokenize(q: string): string[] {
  return q
    .toLowerCase()
    .split(/[^a-z0-9_-]+/)
    .filter((t) => t.length > 1);
}

export class SearchEngine {
  private graph: KnowledgeGraph;

  constructor(private store: CkeStore) {
    this.graph = new KnowledgeGraph(store);
  }

  indexObject(input: {
    orgId: string;
    projectId?: string | null;
    objectType: string;
    objectId: string;
    text: string;
    authority?: number;
    visibility?: string;
    ownerUserId?: string | null;
  }): void {
    const keywords = tokenize(input.text).join(" ");
    this.store.searchIndex = this.store.searchIndex.filter(
      (r) => !(r.objectType === input.objectType && r.objectId === input.objectId),
    );
    this.store.searchIndex.push({
      id: newId("sidx"),
      orgId: input.orgId,
      projectId: input.projectId ?? null,
      objectType: input.objectType,
      objectId: input.objectId,
      text: input.text,
      keywords,
      authority: input.authority ?? 0.5,
      recency: now(),
      visibility: input.visibility ?? "project",
      ownerUserId: input.ownerUserId ?? null,
    });
  }

  /**
   * Hybrid search: keyword + graph expansion + recency + authority + permissions.
   * Embeddings slot is optional and never sole signal.
   */
  search(
    ctx: AuthContext,
    query: string,
    opts: {
      projectId?: string | null;
      limit?: number;
      graphSeedEntityId?: string;
      embeddingScores?: Record<string, number>;
    } = {},
  ): SearchHit[] {
    const terms = tokenize(query);
    const limit = opts.limit ?? 20;
    const hits = new Map<string, SearchHit>();

    for (const row of this.store.searchIndex) {
      if (row.orgId !== ctx.orgId) continue;
      if (opts.projectId != null && row.projectId != null && row.projectId !== opts.projectId) continue;
      const acl = {
        orgId: row.orgId,
        projectId: row.projectId,
        ownerUserId: row.ownerUserId,
        visibility: row.visibility as "private" | "project" | "organization" | "public",
      };
      if (!canRead(ctx, acl)) continue;

      let score = 0;
      const reasons: string[] = [];
      const hay = `${row.text} ${row.keywords}`.toLowerCase();
      let kwHits = 0;
      for (const t of terms) {
        if (hay.includes(t)) kwHits++;
      }
      if (kwHits) {
        score += kwHits / Math.max(1, terms.length);
        reasons.push("keyword");
      }
      const ageHours = (now() - row.recency) / 3_600_000;
      const recencyBoost = Math.max(0, 1 - ageHours / (24 * 30));
      score += 0.15 * recencyBoost;
      if (recencyBoost > 0.5) reasons.push("recency");
      score += 0.2 * row.authority;
      if (row.authority >= 0.7) reasons.push("authority");
      if (opts.projectId && row.projectId === opts.projectId) {
        score += 0.25;
        reasons.push("project_relevance");
      }
      const emb = opts.embeddingScores?.[`${row.objectType}:${row.objectId}`];
      if (emb != null) {
        score += 0.25 * emb;
        reasons.push("embedding");
      }
      if (score <= 0) continue;
      const key = `${row.objectType}:${row.objectId}`;
      const prev = hits.get(key);
      if (!prev || prev.score < score) {
        hits.set(key, {
          objectType: row.objectType,
          objectId: row.objectId,
          score,
          snippet: row.text.slice(0, 240),
          projectId: row.projectId,
          reasons,
        });
      }
    }

    // Graph expansion contributes related entities (not embeddings-alone).
    if (opts.graphSeedEntityId) {
      const trav = this.graph.traverse(ctx, opts.graphSeedEntityId, {
        maxDepth: 1,
        projectId: opts.projectId,
      });
      for (const n of trav.nodes) {
        const key = `entity:${n.entity.id}`;
        const prev = hits.get(key);
        const score = (prev?.score ?? 0) + 0.35 / (n.depth + 1);
        hits.set(key, {
          objectType: "entity",
          objectId: n.entity.id,
          score,
          snippet: n.entity.canonicalName,
          projectId: n.entity.projectId,
          reasons: [...(prev?.reasons ?? []), "knowledge_graph"],
        });
      }
    }

    return [...hits.values()].sort((a, b) => b.score - a.score).slice(0, limit);
  }
}
