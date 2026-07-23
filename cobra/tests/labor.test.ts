import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { planInvestigation, selectStrategy, labor } from "../src/investigator/index.js";

describe("Cobra Labor KC-006", () => {
  it("exposes 14 labor templates", () => {
    assert.equal(labor.listLaborTemplates().length, 14);
    assert.ok(labor.getLaborTemplate("labor_mandatory_overtime"));
  });

  it("plans grievance preparation without LLM", () => {
    const plan = planInvestigation({
      title: "Prepare grievance regarding mandatory overtime",
      templateId: "labor_grievance_preparation",
    });
    assert.equal(plan.templateId, "labor_grievance_preparation");
    assert.ok(plan.questions.length >= 4);
  });

  it("maps labor templates to strategies", () => {
    assert.equal(
      selectStrategy({ title: "x", templateId: "labor_staffing_compliance" }).id,
      "staffing_analysis",
    );
    assert.equal(
      selectStrategy({ title: "x", templateId: "labor_contract_comparison" }).id,
      "evidence_review",
    );
  });

  it("parses articles and searches", () => {
    const body = `ARTICLE 1 Recognition\nThe Employer recognizes the Union.\n\nARTICLE 2 Overtime\nOvertime shall be paid at time and one half.`;
    const articles = labor.parseArticlesFromText("c1", body);
    assert.ok(articles.length >= 2);
    assert.equal(articles[1].topic, "overtime");
    assert.ok(labor.searchArticles(articles, "overtime").length >= 1);
  });

  it("compares contracts without legal conclusions", () => {
    const cmp = labor.compareContractArticles(
      "old",
      "new",
      [{ number: "1", title: "Overtime", text: "time and one half" }],
      [{ number: "1", title: "Overtime", text: "double time after 12" }],
    );
    assert.ok(cmp.diffs.some((d) => d.kind === "modified"));
    assert.ok(/Not a legal interpretation/i.test(cmp.disclaimer));
  });

  it("builds grievance and arbitration drafts with review flags", () => {
    const g = labor.buildGrievanceDraft({
      issue: "Mandatory OT without rotation",
      facts: ["Employee held over on 3 dates"],
      contractArticles: ["Art. 12 Overtime"],
    });
    assert.equal(g.reviewRequired, true);
    assert.ok(/HUMAN REVIEW/i.test(g.draftText));
    const a = labor.buildArbitrationPrep({
      issue: "OT rotation",
      exhibits: [{ id: "e1", label: "Schedule", citationId: "cite_1" }],
    });
    assert.ok(a.exhibitIndexMarkdown.includes("cite_1"));
  });

  it("assesses past practice and reuses staffing metrics", () => {
    const pp = labor.assessPastPractice({
      allegedPractice: "OT rotation by seniority",
      historicalInstances: ["a", "b", "c"],
      durationNotes: "3 years",
    });
    assert.equal(pp.confidence, "medium");
    const staffing = labor.analyzeLaborStaffing({
      authorized: 100,
      filled: 90,
      vacancies: 10,
      minimumStaffing: 95,
      deployable: 88,
    });
    assert.ok(staffing.metrics.some((m) => m.id === "vacancy_rate"));
    assert.ok(staffing.gaps.length >= 0);
  });

  it("builds timeline patterns negotiation and report", () => {
    const tl = labor.buildLaborTimeline([
      { id: "1", at: "2024-01-01", label: "CBA effective", kind: "contract" },
      { id: "2", at: "2023-06-01", label: "Email", kind: "email" },
    ]);
    assert.equal(tl[0].id, "2");
    const patterns = labor.detectLaborPatterns([
      { id: "a", text: "overtime grievance filed" },
      { id: "b", text: "another overtime complaint" },
    ]);
    assert.ok(patterns.some((p) => p.category === "overtime_complaint"));
    const neg = labor.summarizeNegotiation([
      {
        id: "p1",
        side: "union",
        status: "union_proposal",
        articleRefs: ["Art 12"],
        summary: "Increase OT premium",
        openIssues: ["costing"],
      },
    ]);
    assert.ok(neg.openIssues.includes("costing"));
    const tpl = labor.getLaborTemplate("labor_contract_comparison")!;
    const sections = labor.buildLaborReportSections({ title: "Compare MOUs", template: tpl });
    assert.equal(sections.length, labor.LABOR_DEFAULT_REPORT_SECTIONS.length);
    assert.ok(/Not legal advice/i.test(labor.renderLaborMarkdownReport(sections)));
  });

  it("scores labor pilots", () => {
    const s = labor.scoreLaborPilot({ planRelevance: 4, neutrality: 5, wouldUseAgain: true });
    assert.ok(s.average >= 3);
  });
});
