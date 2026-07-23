import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  planInvestigation,
  selectStrategy,
  government,
} from "../src/investigator/index.js";

describe("Cobra Government KC-005", () => {
  it("exposes 15 government templates", () => {
    const list = government.listGovernmentTemplates();
    assert.equal(list.length, 15);
    assert.ok(list.every((t) => t.id.startsWith("gov_")));
    assert.ok(government.getGovernmentTemplate("gov_overtime_analysis"));
  });

  it("plans overtime analysis without LLM and keeps competing hypotheses", () => {
    const plan = planInvestigation({
      title: "Investigate why sheriff overtime increased over the last three fiscal years",
      description: "OT cost and hours rose FY23–FY25",
      templateId: "gov_overtime_analysis",
    });
    assert.equal(plan.templateId, "gov_overtime_analysis");
    assert.ok(plan.questions.length >= 6);
    assert.ok(plan.questions.some((q) => /overtime|vacanc|staff|wage|payroll/i.test(q)));
    assert.ok(plan.evidenceNeeded.some((e) => /overtime|vacanc|position/i.test(e)));
    const tpl = government.getGovernmentTemplate("gov_overtime_analysis")!;
    assert.ok(tpl.defaultHypotheses.length >= 8);
    assert.ok(tpl.defaultHypotheses.some((h) => /Multiple factors/i.test(h)));
  });

  it("maps government templates to strategies", () => {
    const s = selectStrategy({
      title: "Budget variance",
      templateId: "gov_budget_variance",
    });
    assert.equal(s.id, "budget_audit");
    const s2 = selectStrategy({
      title: "Staffing review",
      templateId: "gov_staffing_vacancy",
    });
    assert.equal(s2.id, "staffing_analysis");
  });

  it("normalizes fiscal year and money without silent ambiguity", () => {
    const fy = government.normalizeFiscalYear("2024-25");
    assert.equal(fy.confidence, "confirmed");
    assert.equal(fy.endYear, 2025);
    const money = government.normalizeMoney("($1,200.50)");
    assert.equal(money.confidence, "confirmed");
    assert.ok(money.amount !== null && money.amount < 0);
    const bad = government.normalizeFiscalYear("sometime soon");
    assert.equal(bad.confidence, "unparseable");
  });

  it("computes staffing and overtime metrics only with source fields", () => {
    const staffing = government.computeStaffingMetrics({
      authorized: 100,
      filled: 85,
      citations: ["cite_pos"],
    });
    const vacancy = staffing.find((m) => m.id === "vacancy_rate");
    assert.ok(vacancy);
    assert.equal(vacancy!.confidence, "medium");
    assert.ok(vacancy!.value !== null && Math.abs(vacancy!.value! - 15) < 0.01);

    const otMissing = government.computeOvertimeMetrics({ overtimeHours: 1000 });
    const perEmp = otMissing.find((m) => m.id === "overtime_per_employee");
    assert.equal(perEmp!.confidence, "insufficient");
    assert.equal(perEmp!.value, null);
  });

  it("generates evidence requests and scores pilots", () => {
    const tpl = government.getGovernmentTemplate("gov_overtime_analysis")!;
    const reqs = government.generateEvidenceRequestsFromTemplate(tpl, { prefix: "t" });
    assert.ok(reqs.length >= tpl.requiredEvidenceCategories.length);
    assert.ok(reqs.every((r) => r.status === "needed"));

    const score = government.scorePilot({
      planRelevance: 4,
      evidenceCompleteness: 4,
      citationAccuracy: 5,
      hypothesisQuality: 4,
      findingUsefulness: 4,
      recommendationUsefulness: 3,
      reportClarity: 4,
      neutrality: 5,
      easeOfUse: 4,
      timeSaved: 3,
      wouldUseAgain: true,
      wouldRecommend: true,
    });
    assert.ok(score.average >= 3.5);
    assert.equal(score.blockingDefect, false);

    const saved = government.estimateTimeSaved(null, 2);
    assert.equal(saved.hours, null);
  });

  it("builds government report with disclaimers and 21 sections", () => {
    const tpl = government.getGovernmentTemplate("gov_budget_variance")!;
    const sections = government.buildGovernmentReportSections({
      title: "Three-year budget variance",
      template: tpl,
      metrics: government.computeBudgetMetrics({
        adopted: 100,
        actual: 120,
        period: "FY2025",
        citations: ["cite_b"],
      }),
      hypotheses: tpl.defaultHypotheses,
    });
    assert.equal(sections.length, 21);
    const limitations = sections.find((s) => s.id === "data_limitations")!;
    assert.ok(/Not legal advice/i.test(limitations.body));
    const md = government.renderGovernmentMarkdownReport(sections);
    assert.ok(md.includes("## Findings"));
  });

  it("taxonomy and sensitivity publish warnings", () => {
    assert.ok(government.GOVERNMENT_EVIDENCE_CATEGORIES.length >= 30);
    const warns = government.publishWarningsForSensitivity(["personnel", "public"]);
    assert.ok(warns.some((w) => /personnel/i.test(w)));
    assert.equal(government.requiresPublishReview(["personnel"]), true);
  });

  it("domain definition is government", () => {
    assert.equal(government.GOVERNMENT_DOMAIN.id, "government");
    assert.ok(government.GOVERNMENT_DOMAIN.defaultDisclaimers.length >= 5);
  });
});
