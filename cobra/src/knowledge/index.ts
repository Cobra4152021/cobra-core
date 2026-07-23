import { CitationEngine } from "../citations/index.js";
import { CkeStore } from "../db/store.js";
import { EntityEngine } from "../entity/index.js";
import { KnowledgeGraph } from "../graph/index.js";
import { MemoryEngine } from "../memory/index.js";
import { ReasoningEngine } from "../reasoning/index.js";
import { RelationshipEngine } from "../relationship/index.js";
import { SearchEngine } from "../search/index.js";
import { TimelineEngine } from "../timeline/index.js";
import type { AuthContext, Project, Visibility } from "../types.js";
import { newId, now, slugify } from "../util.js";
import { ConflictEngine } from "./conflicts.js";
import { DecisionEngine } from "./decisions.js";
import { BackgroundJobs } from "../jobs/index.js";
import { Metrics } from "../observability/index.js";

/** Central Cobra Knowledge Engine facade. */
export class KnowledgeEngine {
  readonly store: CkeStore;
  readonly memory: MemoryEngine;
  readonly entities: EntityEngine;
  readonly relationships: RelationshipEngine;
  readonly graph: KnowledgeGraph;
  readonly timeline: TimelineEngine;
  readonly search: SearchEngine;
  readonly citations: CitationEngine;
  readonly decisions: DecisionEngine;
  readonly conflicts: ConflictEngine;
  readonly reasoning: ReasoningEngine;
  readonly jobs: BackgroundJobs;
  readonly metrics: Metrics;

  constructor(store?: CkeStore) {
    this.store = store ?? new CkeStore();
    this.memory = new MemoryEngine(this.store);
    this.entities = new EntityEngine(this.store);
    this.relationships = new RelationshipEngine(this.store);
    this.graph = new KnowledgeGraph(this.store);
    this.timeline = new TimelineEngine(this.store);
    this.search = new SearchEngine(this.store);
    this.citations = new CitationEngine(this.store);
    this.decisions = new DecisionEngine(this.store);
    this.conflicts = new ConflictEngine(this.store);
    this.reasoning = new ReasoningEngine(this.store);
    this.jobs = new BackgroundJobs(this);
    this.metrics = new Metrics(this.store);
  }

  createProject(
    ctx: AuthContext,
    input: { name: string; description?: string; slug?: string; visibility?: Visibility },
  ): Project {
    const ts = now();
    const project: Project = {
      id: newId("proj"),
      orgId: ctx.orgId,
      name: input.name,
      slug: input.slug ?? slugify(input.name),
      description: input.description ?? null,
      ownerUserId: ctx.userId,
      visibility: input.visibility ?? "private",
      createdAt: ts,
      updatedAt: ts,
    };
    this.store.projects.set(project.id, project);
    // Creator receives project scope before seeding graph/timeline objects.
    if (!ctx.projectIds.includes(project.id)) ctx.projectIds.push(project.id);
    // Seed project entity for graph
    this.entities.upsert(ctx, {
      type: "project",
      canonicalName: project.name,
      projectId: project.id,
      description: project.description ?? undefined,
      confidence: 1,
    });
    this.timeline.add(ctx, {
      title: `Project created: ${project.name}`,
      eventType: "project_created",
      occurredAt: ts,
      projectId: project.id,
    });
    this.search.indexObject({
      orgId: ctx.orgId,
      projectId: project.id,
      objectType: "project",
      objectId: project.id,
      text: `${project.name} ${project.description ?? ""}`,
      authority: 1,
      visibility: project.visibility,
      ownerUserId: ctx.userId,
    });
    return project;
  }

  listProjects(ctx: AuthContext): Project[] {
    return [...this.store.projects.values()].filter(
      (p) => p.orgId === ctx.orgId && (ctx.isOrgAdmin || ctx.projectIds.includes(p.id) || p.ownerUserId === ctx.userId),
    );
  }

  getProject(ctx: AuthContext, id: string): Project | null {
    const p = this.store.projects.get(id);
    if (!p || p.orgId !== ctx.orgId) return null;
    if (!ctx.isOrgAdmin && !ctx.projectIds.includes(p.id) && p.ownerUserId !== ctx.userId) return null;
    return p;
  }

  /**
   * Ingest free text: extract entities, infer relationships, store memory + facts index.
   */
  ingestText(
    ctx: AuthContext,
    text: string,
    opts: { projectId?: string | null; source?: string; memoryType?: "research" | "project" | "long_term" } = {},
  ): { memoryId: string; entityIds: string[]; relationshipIds: string[] } {
    const ents = this.entities.extractFromText(ctx, text, opts.projectId);
    const rels = this.relationships.inferFromEntities(
      ctx,
      ents.map((e) => ({ id: e.id, type: e.type })),
      opts.projectId,
    );
    const mem = this.memory.create(ctx, {
      type: opts.memoryType ?? "research",
      content: text,
      projectId: opts.projectId,
      source: opts.source ?? "ingestText",
      confidence: 0.7,
    });
    this.search.indexObject({
      orgId: ctx.orgId,
      projectId: opts.projectId,
      objectType: "memory",
      objectId: mem.id,
      text,
      authority: 0.7,
      visibility: mem.permissions.visibility,
      ownerUserId: ctx.userId,
    });
    for (const e of ents) {
      this.search.indexObject({
        orgId: ctx.orgId,
        projectId: opts.projectId,
        objectType: "entity",
        objectId: e.id,
        text: `${e.canonicalName} ${e.aliases.join(" ")} ${e.description ?? ""}`,
        authority: e.confidence,
        visibility: e.permissions.visibility,
        ownerUserId: ctx.userId,
      });
    }
    return {
      memoryId: mem.id,
      entityIds: ents.map((e) => e.id),
      relationshipIds: rels.map((r) => r.id),
    };
  }
}

export { ConflictEngine, DecisionEngine };
