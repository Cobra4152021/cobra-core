import type { CkeStore } from "../db/store.js";
import { CitationEngine } from "../citations/index.js";
import { ConflictEngine } from "../knowledge/conflicts.js";
import { DecisionEngine } from "../knowledge/decisions.js";
import { EntityEngine } from "../entity/index.js";
import { KnowledgeGraph } from "../graph/index.js";
import { MemoryEngine } from "../memory/index.js";
import { SearchEngine } from "../search/index.js";
import type { AuthContext, InvestigateRequest, InvestigateResult } from "../types.js";
import { now } from "../util.js";

/**
 * Question → project memory → vault/graph/search → merge → reason → store.
 * Does not call external LLMs; produces structured grounded answers.
 */
export class ReasoningEngine {
  private memory: MemoryEngine;
  private entities: EntityEngine;
  private search: SearchEngine;
  private graph: KnowledgeGraph;
  private decisions: DecisionEngine;
  private conflicts: ConflictEngine;
  private citations: CitationEngine;

  constructor(private store: CkeStore) {
    this.memory = new MemoryEngine(store);
    this.entities = new EntityEngine(store);
    this.search = new SearchEngine(store);
    this.graph = new KnowledgeGraph(store);
    this.decisions = new DecisionEngine(store);
    this.conflicts = new ConflictEngine(store);
    this.citations = new CitationEngine(store);
  }

  investigate(ctx: AuthContext, req: InvestigateRequest): InvestigateResult {
    const t0 = now();
    const metrics: Record<string, number> = {};
    const projectId = req.projectId ?? this.inferProjectId(ctx, req.question);
    const minC = req.minConfidence ?? 0.3;

    const tMem = now();
    const memories = this.memory.list(ctx, { projectId }).filter((m) => m.confidence >= minC);
    metrics.memory_ms = now() - tMem;

    const tSearch = now();
    const seed = this.entities
      .list(ctx, { projectId })
      .find((e) => req.question.toLowerCase().includes(e.canonicalName.toLowerCase()));
    const searchHits = this.search.search(ctx, req.question, {
      projectId,
      limit: 15,
      graphSeedEntityId: seed?.id,
    });
    metrics.search_ms = now() - tSearch;

    const tGraph = now();
    const graphNodes = seed
      ? this.graph.traverse(ctx, seed.id, {
          maxDepth: req.maxDepth ?? 2,
          projectId,
          minConfidence: minC,
        }).nodes
      : [];
    metrics.graph_ms = now() - tGraph;

    const decisions = this.decisions.list(ctx, projectId);
    const openConflicts = this.conflicts.listOpen(ctx, projectId);
    const facts = [...this.store.facts.values()].filter(
      (f) => f.orgId === ctx.orgId && (projectId == null || f.projectId === projectId),
    );

    // Deduplicate by content hash / id
    const memIds = [...new Set(memories.map((m) => m.id))];
    const entIds = [...new Set(graphNodes.map((n) => n.entity.id))];
    const factIds = [...new Set(facts.map((f) => f.id))];

    const citationMap = new Map<string, (typeof memories)[0]["citations"][0]>();
    for (const m of memories) for (const c of m.citations) citationMap.set(c.id, c);
    for (const f of facts) for (const c of f.citations) citationMap.set(c.id, c);
    for (const d of decisions) for (const c of d.citations) citationMap.set(c.id, c);

    const answer = this.composeAnswer(req.question, {
      memories,
      entities: graphNodes.map((n) => n.entity),
      facts,
      decisions,
      conflicts: openConflicts,
      searchHits,
    });

    // Store new research memory from this investigation
    const stored = this.memory.create(ctx, {
      type: "research",
      content: `Investigation: ${req.question}\nResult summary: ${answer.slice(0, 500)}`,
      projectId,
      source: "reasoning.investigate",
      confidence: openConflicts.length ? 0.45 : 0.65,
      citations: [...citationMap.values()],
    });
    this.search.indexObject({
      orgId: ctx.orgId,
      projectId,
      objectType: "memory",
      objectId: stored.id,
      text: stored.content,
      authority: stored.confidence,
      visibility: stored.permissions.visibility,
      ownerUserId: ctx.userId,
    });

    metrics.total_ms = now() - t0;
    return {
      answer,
      projectId,
      memoriesUsed: memIds,
      entitiesUsed: entIds,
      factsUsed: factIds,
      citations: [...citationMap.values()],
      conflicts: openConflicts,
      decisions,
      searchHits,
      newKnowledgeStored: [stored.id],
      metrics,
    };
  }

  private inferProjectId(ctx: AuthContext, question: string): string | null {
    const q = question.toLowerCase();
    for (const p of this.store.projects.values()) {
      if (p.orgId !== ctx.orgId) continue;
      if (q.includes(p.name.toLowerCase()) || q.includes(p.slug.toLowerCase())) return p.id;
    }
    return ctx.projectIds[0] ?? null;
  }

  private composeAnswer(
    question: string,
    ctx: {
      memories: { content: string; confidence: number }[];
      entities: { canonicalName: string; type: string; description?: string | null }[];
      facts: { statement: string; confidence: number }[];
      decisions: { title: string; status: string; reason?: string | null }[];
      conflicts: { summary: string }[];
      searchHits: { snippet: string; score: number; reasons: string[] }[];
    },
  ): string {
    const lines: string[] = [];
    lines.push(`Question: ${question}`);
    if (ctx.conflicts.length) {
      lines.push("");
      lines.push("Open conflicts (not silently resolved):");
      for (const c of ctx.conflicts.slice(0, 5)) lines.push(`- ${c.summary}`);
    }
    if (ctx.decisions.length) {
      lines.push("");
      lines.push("Relevant decisions:");
      for (const d of ctx.decisions.slice(0, 5)) {
        lines.push(`- [${d.status}] ${d.title}${d.reason ? ` — why: ${d.reason}` : ""}`);
      }
    }
    if (ctx.facts.length) {
      lines.push("");
      lines.push("Known facts:");
      for (const f of ctx.facts.slice(0, 8)) lines.push(`- (${f.confidence.toFixed(2)}) ${f.statement}`);
    }
    if (ctx.entities.length) {
      lines.push("");
      lines.push("Related entities:");
      for (const e of ctx.entities.slice(0, 8)) {
        lines.push(`- ${e.canonicalName} [${e.type}]${e.description ? `: ${e.description}` : ""}`);
      }
    }
    if (ctx.memories.length) {
      lines.push("");
      lines.push("Project / research memory:");
      for (const m of ctx.memories.slice(0, 5)) lines.push(`- ${m.content.slice(0, 200)}`);
    }
    if (ctx.searchHits.length) {
      lines.push("");
      lines.push("Hybrid search hits:");
      for (const h of ctx.searchHits.slice(0, 5)) {
        lines.push(`- (${h.score.toFixed(2)} via ${h.reasons.join("+")}) ${h.snippet}`);
      }
    }
    if (lines.length === 1) {
      lines.push("");
      lines.push("No grounded knowledge found yet. Ingest documents or memories first.");
    }
    lines.push("");
    lines.push("Citations: only IDs present in Evidence Vault / citation store are attached; none invented.");
    return lines.join("\n");
  }
}
