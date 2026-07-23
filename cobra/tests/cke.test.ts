import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { CkeApi, KnowledgeEngine, type AuthContext } from "../src/index.js";

function ctx(overrides: Partial<AuthContext> = {}): AuthContext {
  return {
    orgId: "org_1",
    userId: "user_1",
    projectIds: [],
    ...overrides,
  };
}

describe("Cobra Knowledge Engine KC-003", () => {
  it("creates project-aware memory and entities", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Hidden Grid", description: "Census OS" });
    c.projectIds.push(project.id);
    const mem = ke.memory.create(c, {
      type: "project",
      content: "Hidden Grid uses Cloudflare Workers and D1.",
      projectId: project.id,
      source: "test",
    });
    assert.equal(mem.projectId, project.id);
    const ingested = ke.ingestText(
      c,
      "King Cobra depends on GPT-OSS and SigLIP for Cobra Core vision.",
      { projectId: project.id },
    );
    assert.ok(ingested.entityIds.length >= 2);
    assert.ok(ke.entities.list(c, { projectId: project.id }).some((e) => e.canonicalName === "GPT-OSS"));
  });

  it("builds relationships and traverses graph with depth limit", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Cobra" });
    c.projectIds.push(project.id);
    ke.ingestText(c, "Cobra depends on GPT-OSS technology and Benchmark Lab.", {
      projectId: project.id,
    });
    const projectEnt = ke.entities.list(c, { projectId: project.id, type: "project" })[0];
    const g = ke.graph.traverse(c, projectEnt.id, { maxDepth: 1, projectId: project.id });
    assert.ok(g.nodes.length >= 1);
    assert.ok(g.edges.length >= 1);
    const deep = ke.graph.traverse(c, projectEnt.id, { maxDepth: 0, projectId: project.id });
    assert.equal(deep.nodes.length, 1);
  });

  it("enforces no cross-project leakage", () => {
    const ke = new KnowledgeEngine();
    const owner = ctx({ userId: "u1" });
    const p1 = ke.createProject(owner, { name: "Alpha" });
    const p2 = ke.createProject(owner, { name: "Beta" });
    owner.projectIds.push(p1.id, p2.id);
    ke.memory.create(owner, {
      type: "project",
      content: "secret alpha",
      projectId: p1.id,
      source: "t",
      visibility: "project",
    });
    const outsider = ctx({ userId: "u2", projectIds: [p2.id] });
    const visible = ke.memory.list(outsider, { projectId: p1.id });
    assert.equal(visible.length, 0);
  });

  it("hybrid search uses keyword + project relevance not embeddings alone", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Union Book" });
    c.projectIds.push(project.id);
    ke.ingestText(c, "Union Book stores labor history documents in Evidence Vault.", {
      projectId: project.id,
    });
    const hits = ke.search.search(c, "Evidence Vault labor", { projectId: project.id });
    assert.ok(hits.length > 0);
    assert.ok(hits[0].reasons.includes("keyword") || hits[0].reasons.includes("project_relevance"));
  });

  it("timeline orders chronologically", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Argentina Farm" });
    c.projectIds.push(project.id);
    ke.timeline.add(c, {
      title: "Later",
      eventType: "note",
      occurredAt: 2000,
      projectId: project.id,
    });
    ke.timeline.add(c, {
      title: "Earlier",
      eventType: "note",
      occurredAt: 1000,
      projectId: project.id,
    });
    const events = ke.timeline.list(c, { projectId: project.id }).filter((e) => e.eventType === "note");
    assert.equal(events[0].title, "Earlier");
    assert.equal(events[1].title, "Later");
  });

  it("never invents citations", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    assert.throws(() => ke.citations.create(c, { evidenceKind: "doc" }), /requires/);
    const cite = ke.citations.create(c, {
      evidenceKind: "document",
      documentHash: "abc123",
      excerpt: "line proof",
      page: 2,
    });
    assert.equal(cite.documentHash, "abc123");
    assert.throws(() => ke.citations.resolveAll(["nope"]), /Unknown citation/);
  });

  it("records decisions and surfaces fact conflicts", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Cobra Core" });
    c.projectIds.push(project.id);
    ke.decisions.record(c, {
      title: "Use GPT-OSS",
      status: "approved",
      reason: "Open weights; lower inference cost",
      alternatives: ["Gemma", "Qwen", "Claude"],
      projectId: project.id,
    });
    ke.conflicts.storeFact(c, "GPT-OSS is the language foundation", { projectId: project.id });
    ke.conflicts.storeFact(c, "GPT-OSS is not the language foundation", { projectId: project.id });
    const conflicts = ke.conflicts.detectFactConflicts(c, project.id);
    assert.ok(conflicts.some((x) => x.conflictType === "contradictory_facts"));
  });

  it("investigate pipeline stores new research memory", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const project = ke.createProject(c, { name: "Leadership Series" });
    c.projectIds.push(project.id);
    ke.ingestText(c, "Leadership Series uses Claude for writing assistance.", {
      projectId: project.id,
    });
    ke.decisions.record(c, {
      title: "Use Claude for drafts",
      status: "approved",
      reason: "Writing quality",
      projectId: project.id,
    });
    const result = ke.reasoning.investigate(c, {
      question: "Why does Leadership Series use Claude?",
      projectId: project.id,
    });
    assert.match(result.answer, /decision|Claude|Leadership/i);
    assert.ok(result.newKnowledgeStored.length >= 1);
    assert.ok(result.decisions.length >= 1);
  });

  it("API routes are additive and permission-safe", async () => {
    const ke = new KnowledgeEngine();
    const api = new CkeApi(ke);
    const c = ctx();
    const created = await api.handle({
      method: "POST",
      path: "/project",
      ctx: c,
      body: { name: "CKE Demo" },
    });
    assert.equal(created.status, 201);
    const projectId = (created.body as { project: { id: string } }).project.id;
    c.projectIds.push(projectId);
    const inv = await api.handle({
      method: "POST",
      path: "/investigate",
      ctx: c,
      body: { question: "What is CKE Demo?", projectId },
    });
    assert.equal(inv.status, 200);
    const forbidden = await api.handle({
      method: "GET",
      path: "/memory",
      ctx: ctx({ userId: "other", projectIds: [] }),
      query: { projectId },
    });
    assert.equal(forbidden.status, 200);
    assert.equal((forbidden.body as { memories: unknown[] }).memories.length, 0);
  });

  it("metrics snapshot reports graph and memory sizes", () => {
    const ke = new KnowledgeEngine();
    const c = ctx();
    const p = ke.createProject(c, { name: "Metrics" });
    c.projectIds.push(p.id);
    ke.ingestText(c, "Metrics project uses Cloudflare Workers.", { projectId: p.id });
    const snap = ke.metrics.snapshot("org_1");
    assert.ok(snap.entity_count >= 1);
    assert.ok(snap.memory_size >= 1);
  });
});
