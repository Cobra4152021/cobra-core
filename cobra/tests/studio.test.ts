import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { studio } from "../src/investigator/index.js";

describe("Cobra Intelligence Studio KC-007", () => {
  it("exposes studio domain metadata and disclaimers", () => {
    assert.equal(studio.STUDIO_DOMAIN_ID, "studio");
    assert.equal(studio.STUDIO_DOMAIN_VERSION, "0.1.0");
    assert.ok(studio.STUDIO_DISCLAIMERS.some((d) => /visualization only/i.test(d)));
    assert.ok(studio.STUDIO_DISCLAIMERS.some((d) => /Not legal advice/i.test(d)));
    assert.ok(studio.STUDIO_DISCLAIMERS.some((d) => /Human review required/i.test(d)));
  });

  it("builds executive dashboard from raw counts", () => {
    const dash = studio.buildExecutiveDashboard({
      openInvestigations: 3,
      completed: 7,
      evidenceCount: 42,
      pendingEvidence: 5,
      highRiskCases: 2,
      reviewRequired: 4,
      recentlyUpdated: [
        { id: "i1", title: "Older", updatedAt: "2026-01-01", kind: "investigation" },
        { id: "i2", title: "Newer", updatedAt: "2026-02-01", kind: "report" },
      ],
      performanceSummary: { avgInvestigationDays: 14, evidenceCompletionRate: 88, reviewBacklog: 2 },
      pilotScoresSummary: { totalPilots: 2, activePilots: 1, avgScore: 0.82 },
    });
    assert.equal(dash.openInvestigations, 3);
    assert.equal(dash.completed, 7);
    assert.equal(dash.recentlyUpdated[0]?.id, "i2");
    assert.equal(dash.performanceSummary.reviewBacklog, 2);
    assert.equal(dash.pilotScoresSummary.activePilots, 1);
  });

  it("filters studio timeline by kind and query", () => {
    const events = studio.buildStudioTimeline([
      { id: "e1", at: "2026-01-10", label: "Budget memo", kind: "budget" },
      { id: "e2", at: "2026-01-15", label: "Staffing report", kind: "staffing" },
      { id: "e3", at: "2026-01-20", label: "Grievance filed", kind: "grievance" },
    ]);
    const filtered = studio.filterStudioTimeline(events, {
      kinds: ["budget", "grievance"],
      q: "grievance",
    });
    assert.equal(filtered.length, 1);
    assert.equal(filtered[0]?.kind, "grievance");
  });

  it("highlights graph neighborhood around a node", () => {
    const graph = studio.buildRelationshipGraph(
      [
        { id: "n1", type: "investigation", label: "Case A" },
        { id: "n2", type: "evidence", label: "Doc 1" },
        { id: "n3", type: "people", label: "Witness" },
      ],
      [
        { id: "e1", sourceId: "n1", targetId: "n2", label: "cites" },
        { id: "e2", sourceId: "n2", targetId: "n3", label: "mentions" },
      ],
    );
    const hood = studio.highlightNeighborhood(graph, "n1", 2);
    assert.ok(hood.nodeIds.includes("n1"));
    assert.ok(hood.nodeIds.includes("n3"));
    assert.equal(hood.edges.length, 2);
  });

  it("searches unified studio index", () => {
    const index = studio.buildUnifiedSearchIndex([
      {
        id: "h1",
        kind: "investigation",
        title: "Overtime review",
        snippet: "Mandatory OT rotation",
        updatedAt: "2026-02-01",
      },
      {
        id: "h2",
        kind: "contract",
        title: "CBA 2024",
        snippet: "Article 12 overtime",
        updatedAt: "2026-01-01",
      },
    ]);
    const hits = studio.searchStudioIndex(index, { q: "overtime", kinds: ["investigation"] });
    assert.equal(hits.length, 1);
    assert.equal(hits[0]?.id, "h1");
  });

  it("compares investigations with shared and unique items", () => {
    const result = studio.compareInvestigations(
      {
        id: "a",
        title: "Case A",
        findings: [{ id: "f1", label: "Finding 1" }],
        evidence: [{ id: "ev1", label: "Doc" }],
        metrics: [],
        recommendations: [],
        confidence: 0.7,
        missingEvidence: [{ id: "m1", label: "Payroll" }],
      },
      {
        id: "b",
        title: "Case B",
        findings: [{ id: "f1", label: "Finding 1" }, { id: "f2", label: "Finding 2" }],
        evidence: [],
        metrics: [],
        recommendations: [],
        confidence: 0.9,
        missingEvidence: [],
      },
    );
    const findings = result.highlights.find((h) => h.field === "findings");
    assert.equal(findings?.shared.length, 1);
    assert.equal(findings?.onlyInB.length, 1);
    assert.equal(result.confidenceDelta, 0.2);
    assert.ok(/Not a merged finding/i.test(result.disclaimer));
  });

  it("returns report designer export placeholder", () => {
    const layout = studio.composeReportLayout(["cover", "findings", "citations"]);
    assert.equal(layout.orderedSectionIds.length, 3);
    const exp = studio.exportReportPlaceholder();
    assert.equal(exp.exportStatus, "placeholder");
    assert.match(exp.message, /Export pipeline not enabled/i);
  });

  it("defines studio navigation with ten items", () => {
    assert.equal(studio.STUDIO_NAV.length, 10);
    assert.ok(studio.STUDIO_NAV.some((n) => n.label === "Dashboard"));
    assert.ok(studio.STUDIO_NAV.some((n) => n.label === "Settings"));
  });
});
