import type { KnowledgeEngine } from "../knowledge/index.js";
import { PermissionError } from "../permissions/index.js";
import type { AuthContext, DecisionStatus, InvestigateRequest, MemoryType } from "../types.js";

export type HttpMethod = "GET" | "POST";

export interface ApiRequest {
  method: HttpMethod;
  path: string;
  query?: Record<string, string | undefined>;
  body?: unknown;
  ctx: AuthContext;
}

export interface ApiResponse {
  status: number;
  body: unknown;
}

/**
 * Framework-agnostic HTTP handler for CKE.
 * Mount under /api/cke/* in Workers later — does not touch chat routing.
 */
export class CkeApi {
  constructor(private ke: KnowledgeEngine) {}

  async handle(req: ApiRequest): Promise<ApiResponse> {
    try {
      return this.route(req);
    } catch (err) {
      if (err instanceof PermissionError) {
        return { status: 403, body: { ok: false, error: err.message } };
      }
      const message = err instanceof Error ? err.message : "error";
      return { status: 400, body: { ok: false, error: message } };
    }
  }

  /** Async generator for streaming investigate tokens (answer chunks). */
  async *streamInvestigate(ctx: AuthContext, body: InvestigateRequest): AsyncGenerator<string> {
    const t0 = Date.now();
    const result = this.ke.reasoning.investigate(ctx, body);
    this.ke.metrics.observe("reasoning", Date.now() - t0);
    const chunkSize = 120;
    for (let i = 0; i < result.answer.length; i += chunkSize) {
      yield result.answer.slice(i, i + chunkSize);
    }
    yield `\n\n__META__${JSON.stringify({
      citations: result.citations.map((c) => c.id),
      conflicts: result.conflicts.map((c) => c.id),
      newKnowledgeStored: result.newKnowledgeStored,
      metrics: result.metrics,
    })}`;
  }

  private route(req: ApiRequest): ApiResponse {
    const { method, path, ctx } = req;
    const body = (req.body ?? {}) as Record<string, unknown>;
    const q = req.query ?? {};

    if (method === "GET" && path === "/projects") {
      return { status: 200, body: { ok: true, projects: this.ke.listProjects(ctx) } };
    }
    if (method === "GET" && path.startsWith("/projects/")) {
      const id = path.slice("/projects/".length);
      const p = this.ke.getProject(ctx, id);
      if (!p) return { status: 404, body: { ok: false, error: "Not found" } };
      return { status: 200, body: { ok: true, project: p } };
    }
    if (method === "POST" && path === "/project") {
      const project = this.ke.createProject(ctx, {
        name: String(body.name ?? ""),
        description: body.description ? String(body.description) : undefined,
        slug: body.slug ? String(body.slug) : undefined,
      });
      ctx.projectIds.push(project.id);
      return { status: 201, body: { ok: true, project } };
    }
    if (method === "GET" && path === "/memory") {
      return {
        status: 200,
        body: {
          ok: true,
          memories: this.ke.memory.list(ctx, {
            projectId: q.projectId,
            type: q.type as MemoryType | undefined,
          }),
        },
      };
    }
    if (method === "POST" && path === "/memory") {
      const mem = this.ke.memory.create(ctx, {
        type: (body.type as MemoryType) ?? "research",
        content: String(body.content ?? ""),
        projectId: (body.projectId as string) ?? null,
        source: String(body.source ?? "api"),
        confidence: body.confidence != null ? Number(body.confidence) : undefined,
      });
      return { status: 201, body: { ok: true, memory: mem } };
    }
    if (method === "GET" && path === "/entities") {
      return {
        status: 200,
        body: { ok: true, entities: this.ke.entities.list(ctx, { projectId: q.projectId }) },
      };
    }
    if (method === "POST" && path === "/entity") {
      const ent = this.ke.entities.upsert(ctx, {
        type: body.type as never,
        canonicalName: String(body.canonicalName ?? body.name ?? ""),
        projectId: (body.projectId as string) ?? null,
        description: body.description ? String(body.description) : undefined,
        aliases: Array.isArray(body.aliases) ? body.aliases.map(String) : undefined,
      });
      return { status: 201, body: { ok: true, entity: ent } };
    }
    if (method === "GET" && path === "/relationships") {
      return {
        status: 200,
        body: { ok: true, relationships: this.ke.relationships.list(ctx, { projectId: q.projectId }) },
      };
    }
    if (method === "POST" && path === "/relationship") {
      const rel = this.ke.relationships.create(ctx, {
        fromEntityId: String(body.fromEntityId),
        toEntityId: String(body.toEntityId),
        relType: String(body.relType),
        projectId: (body.projectId as string) ?? null,
        evidence: Array.isArray(body.evidence) ? body.evidence.map(String) : undefined,
      });
      return { status: 201, body: { ok: true, relationship: rel } };
    }
    if (method === "GET" && path === "/graph") {
      const entityId = q.entityId;
      if (!entityId) return { status: 400, body: { ok: false, error: "entityId required" } };
      const g = this.ke.graph.traverse(ctx, entityId, {
        maxDepth: q.depth ? Number(q.depth) : 2,
        projectId: q.projectId,
        minConfidence: q.minConfidence ? Number(q.minConfidence) : 0,
      });
      return { status: 200, body: { ok: true, graph: g } };
    }
    if (method === "GET" && path === "/search") {
      const query = q.q ?? "";
      const t0 = Date.now();
      const hits = this.ke.search.search(ctx, query, { projectId: q.projectId });
      this.ke.metrics.observe("search", Date.now() - t0);
      return { status: 200, body: { ok: true, hits } };
    }
    if (method === "GET" && path === "/timeline") {
      const t0 = Date.now();
      const events = this.ke.timeline.list(ctx, {
        projectId: q.projectId,
        entityId: q.entityId,
      });
      this.ke.metrics.observe("timeline", Date.now() - t0);
      return { status: 200, body: { ok: true, events } };
    }
    if (method === "POST" && path === "/investigate") {
      const t0 = Date.now();
      const result = this.ke.reasoning.investigate(ctx, {
        question: String(body.question ?? ""),
        projectId: (body.projectId as string) ?? null,
        maxDepth: body.maxDepth != null ? Number(body.maxDepth) : undefined,
      });
      this.ke.metrics.observe("reasoning", Date.now() - t0);
      return { status: 200, body: { ok: true, result } };
    }
    if (method === "POST" && path === "/decision") {
      const d = this.ke.decisions.record(ctx, {
        title: String(body.title ?? ""),
        status: (body.status as DecisionStatus) ?? "proposed",
        reason: body.reason ? String(body.reason) : undefined,
        alternatives: Array.isArray(body.alternatives) ? body.alternatives.map(String) : undefined,
        projectId: (body.projectId as string) ?? null,
      });
      return { status: 201, body: { ok: true, decision: d } };
    }
    if (method === "GET" && path === "/metrics") {
      return { status: 200, body: { ok: true, metrics: this.ke.metrics.snapshot(ctx.orgId) } };
    }
    return { status: 404, body: { ok: false, error: "Not found" } };
  }
}
