import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  research,
  sdk,
} from "../src/investigator/index.js";
import {
  createDefaultRegistry,
  createResearchPackRegistration,
  planInstall,
  buildMarketplaceCatalog,
  createAllBuiltInPacks,
  assertSandboxSafe,
} from "../src/investigator/sdk/index.js";

describe("Cobra Research KC-009", () => {
  it("exposes 9 research templates", () => {
    const templates = research.listResearchTemplates();
    assert.equal(templates.length, 9);
    assert.ok(research.getResearchTemplate("research_anomaly_investigation"));
    assert.ok(templates.every((t) => t.id.startsWith("research_")));
  });

  it("scores peer-reviewed sources higher than anonymous sources", () => {
    const peer = research.assessSourceReliability({
      kind: "peer_reviewed_paper",
      year: 2024,
      peerReviewed: true,
      currentYear: 2025,
    });
    const anon = research.assessSourceReliability({
      kind: "anonymous_source",
      year: 2024,
      currentYear: 2025,
    });
    assert.equal(peer.overall, "high");
    assert.equal(anon.overall, "low");
    assert.ok(/heuristic/i.test(peer.disclaimer));
  });

  it("summarizes evidence matrix", () => {
    const matrix = research.buildEvidenceMatrix([
      { id: "r1", claim: "A", sourceId: "s1", relation: "supports" },
      { id: "r2", claim: "B", sourceId: "s2", relation: "contradicts" },
      { id: "r3", claim: "C", sourceId: "s3", relation: "missing" },
    ]);
    const summary = research.summarizeMatrix(matrix);
    assert.equal(summary.totalRows, 3);
    assert.equal(summary.supports, 1);
    assert.equal(summary.contradicts, 1);
    assert.equal(summary.missing, 1);
    assert.ok(summary.conflictRatio > 0);
  });

  it("builds hypothesis workspace with competing hypotheses", () => {
    const ws = research.buildHypothesisWorkspace({ issue: "Unexplained signal" });
    assert.equal(ws.reviewRequired, true);
    assert.ok(ws.hypotheses.length >= 3);
    assert.ok(ws.hypotheses.some((h) => /insufficient/i.test(h.statement)));
  });

  it("filters research timeline", () => {
    const timeline = research.buildResearchTimeline([
      { id: "e1", at: "2020-01-01", kind: "publication", label: "Paper A" },
      { id: "e2", at: "2021-06-01", kind: "sighting", label: "Event B" },
      { id: "e3", at: "2022-03-01", kind: "field_observation", label: "Field C" },
    ]);
    const filtered = research.filterResearchTimeline(timeline, {
      kinds: ["sighting", "field_observation"],
      after: "2021-01-01",
    });
    assert.equal(filtered.length, 2);
    assert.ok(filtered.every((e) => e.at >= "2021-01-01"));
  });

  it("explores citation graph neighborhood", () => {
    const graph = research.buildCitationGraph({
      nodes: [
        { id: "n1", kind: "papers", label: "Paper 1", citationId: "cite_1" },
        { id: "n2", kind: "books", label: "Book 2", citationId: "cite_2" },
        { id: "n3", kind: "web", label: "Web 3", citationId: null },
      ],
      links: [
        { from: "n1", to: "n2", relation: "cites" },
        { from: "n2", to: "n3", relation: "related" },
      ],
    });
    const hood = research.exploreNeighborhood(graph, "n1", 1);
    assert.equal(hood.centerId, "n1");
    assert.ok(hood.nodes.some((n) => n.id === "n2"));
    assert.ok(hood.links.length >= 1);
  });

  it("builds report sections with disclaimers", () => {
    const template = research.getResearchTemplate("research_literature_review")!;
    const sections = research.buildResearchReportSections({
      title: "Lit review",
      template,
      findings: ["Finding one"],
    });
    assert.equal(sections.length, research.RESEARCH_DEFAULT_REPORT_SECTIONS.length);
    const md = research.renderResearchMarkdownReport(sections);
    assert.ok(/Not scientific peer review/i.test(md));
    assert.ok(/Human review required/i.test(md));
  });

  it("computes research metrics from counts", () => {
    const metrics = research.computeResearchMetrics({
      evidenceCount: 10,
      citedSourceCount: 8,
      totalSourceCount: 10,
      hypothesisCount: 4,
      highConfidenceHypothesisCount: 2,
      requiredCategoryCount: 5,
      coveredCategoryCount: 4,
      uniqueSourceKinds: 6,
      totalSourceKinds: 8,
      supportingRelations: 7,
      contradictingRelations: 3,
    });
    assert.equal(metrics.length, 6);
    assert.ok(metrics.some((m) => m.id === "evidence_density" && m.value === 1));
    assert.ok(metrics.some((m) => m.id === "evidence_conflicts" && m.value > 0));
  });

  it("registers cobra.research via default registry with templates", () => {
    const registry = createDefaultRegistry();
    const pack = registry.getPack("cobra.research");
    assert.ok(pack);
    assert.equal(pack!.templates.length, 9);
    assert.ok(pack!.templates.some((t) => t.id === "research_anomaly_investigation"));
    assert.ok(pack!.reportLayouts.some((l) => l.id === "research.default"));
    assert.equal(pack!.category, "Research");
  });

  it("includes research in marketplace catalog as installable", () => {
    const packs = createAllBuiltInPacks();
    assert.ok(packs.some((p) => p.packId === "cobra.research"));

    const researchPack = createResearchPackRegistration();
    assert.doesNotThrow(() => assertSandboxSafe(researchPack.manifest));

    const catalog = buildMarketplaceCatalog({
      packs,
      installedPackIds: [],
      disabledPackIds: [],
    });
    const entry = catalog.find((e) => e.packId === "cobra.research");
    assert.ok(entry);
    assert.equal(entry!.category, "Research");
    assert.equal(entry!.status, "available");
    assert.equal(entry!.templateCount, 9);

    const install = planInstall(researchPack, [], "0.4.1", packs.map((r) => ({
      packId: r.packId,
      registration: r,
    })));
    assert.equal(install.success, true);
    if (install.success) {
      assert.ok(install.plan.permissionsGranted.includes("research.templates.read"));
    }
  });

  it("registers research pack via registerResearchPack", () => {
    const registry = new sdk.DomainPackRegistry();
    research.registerResearchPack(registry);
    assert.ok(registry.getPack("cobra.research"));
  });
});
