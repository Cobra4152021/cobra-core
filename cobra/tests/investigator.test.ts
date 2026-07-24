import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  planInvestigation,
  buildFindings,
  buildRecommendations,
  buildReportSections,
  renderMarkdownReport,
  INVESTIGATION_TEMPLATES,
} from "../src/investigator/index.js";

describe("Cobra Investigator KC-004", () => {
  it("plans overtime investigation without LLM", () => {
    const plan = planInvestigation({
      title: "Investigate why overtime increased",
      description: "OT rose in Q3",
      templateId: "union_audit",
    });
    assert.ok(plan.questions.length >= 4);
    assert.ok(plan.questions.some((q) => /staff|vacanc|budget|overtime|contract|historical/i.test(q)));
    assert.ok(plan.steps[0].toLowerCase().includes("scope"));
    assert.equal(plan.templateId, "union_audit");
    assert.ok(plan.evidenceNeeded.length >= 3);
  });

  it("exposes built-in templates", () => {
    assert.ok(INVESTIGATION_TEMPLATES.length >= 9);
  });

  it("builds findings with citation allowlist only", () => {
    const findings = buildFindings({
      questions: ["What staffing existed?"],
      evidence: [
        {
          id: "e1",
          kind: "memory",
          label: "staffing note",
          excerpt: "Vacancies rose",
          citationId: "cite_ok",
        },
        {
          id: "e2",
          kind: "memory",
          label: "forged cite attempt",
          citationId: "cite_FORGED",
        },
      ],
      conflicts: [{ summary: "Vacancy counts disagree" }],
      allowedCitationIds: ["cite_ok"],
    });
    const cites = findings.flatMap((f) => f.citations);
    assert.ok(cites.includes("cite_ok"));
    assert.ok(!cites.includes("cite_FORGED"));
    assert.ok(findings.some((f) => /conflict/i.test(f.title)));
  });

  it("marks insufficient evidence when empty", () => {
    const findings = buildFindings({
      questions: ["Why?"],
      evidence: [],
      conflicts: [],
      allowedCitationIds: [],
    });
    assert.equal(findings[0].confidence, "insufficient_evidence");
  });

  it("builds recommendations and markdown report", () => {
    const plan = planInvestigation({ title: "Budget variance", templateId: "budget_audit" });
    const findings = buildFindings({
      questions: plan.questions.slice(0, 2),
      evidence: [{ id: "e1", kind: "fact", label: "variance 12%", excerpt: "12% over" }],
      conflicts: [],
      allowedCitationIds: [],
    });
    const recs = buildRecommendations(findings);
    assert.ok(recs.length >= 1);
    const sections = buildReportSections({
      title: "Budget variance",
      plan,
      evidenceLabels: ["variance 12%"],
      timelineLines: ["2024-01 budget approved"],
      findings,
      conflicts: [],
      recommendations: recs,
      allowedCitationIds: [],
    });
    const md = renderMarkdownReport("Budget variance", sections);
    assert.match(md, /Executive Summary/);
    assert.match(md, /Findings/);
    assert.match(md, /Citations/);
  });
});
