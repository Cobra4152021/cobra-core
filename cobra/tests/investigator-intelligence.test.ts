import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  selectStrategy,
  listStrategies,
  planInvestigation,
  scoreEvidenceQuality,
  buildCompetingHypotheses,
  detectMissingEvidence,
  buildConfidenceBundle,
  buildReviewChecklist,
  buildInvestigationMetrics,
  buildFindings,
  buildRecommendations,
  buildReportSections,
  renderMarkdownReport,
} from "../src/investigator/index.js";

describe("Cobra Investigator KC-004B Intelligence", () => {
  it("selects union contract strategy for overtime", () => {
    const s = selectStrategy({ title: "Investigate why overtime increased" });
    assert.equal(s.id, "union_contract_review");
    assert.ok(listStrategies().length >= 8);
  });

  it("plans with strategy metadata", () => {
    const plan = planInvestigation({
      title: "Investigate why overtime increased",
      templateId: "union_audit",
    });
    assert.equal(plan.strategyId, "union_contract_review");
    assert.ok(plan.methodology && plan.methodology.length >= 3);
    assert.ok(plan.confidenceRules && plan.confidenceRules.length >= 1);
  });

  it("scores evidence quality dimensions", () => {
    const summary = scoreEvidenceQuality({
      queryText: "overtime vacancy staffing",
      evidence: [
        {
          id: "e1",
          kind: "contract",
          label: "Collective agreement OT limits",
          excerpt: "Official approved overtime limits for 2024 staffing",
          citationId: "cite_1",
        },
        {
          id: "e2",
          kind: "search",
          label: "draft note",
          excerpt: "approx",
        },
      ],
    });
    assert.equal(summary.scores.length, 2);
    assert.ok(summary.scores[0].dimensions.authority > 0);
    assert.ok(summary.meanOverall > 0);
    assert.ok(summary.scores[0].overall > summary.scores[1].overall);
  });

  it("builds multiple competing hypotheses", () => {
    const strategy = selectStrategy({ title: "Investigate why overtime increased" });
    const hyps = buildCompetingHypotheses({
      title: "Investigate why overtime increased",
      questions: strategy.questions,
      strategy,
      evidence: [
        {
          id: "e1",
          kind: "memory",
          label: "vacancy rose",
          excerpt: "Vacancies rose in Q3",
        },
      ],
      conflicts: [{ summary: "Vacancy counts disagree between sources" }],
      missingEvidence: ["payroll extracts"],
    });
    assert.ok(hyps.length >= 2);
    assert.ok(hyps.every((h) => h.title && h.confidence));
  });

  it("detects missing evidence categories", () => {
    const strategy = selectStrategy({ title: "Investigate why overtime increased" });
    const missing = detectMissingEvidence({
      strategy,
      evidence: [],
      evidenceNeeded: strategy.evidencePriorities,
      timelineLines: [],
    });
    assert.ok(missing.items.length >= 3);
    assert.ok(missing.evidenceNeededSection.length >= 3);
    assert.ok(missing.items.some((i) => i.category === "timeline_gap"));
  });

  it("builds separated confidence and review checklist", () => {
    const strategy = selectStrategy({ title: "Budget variance review" });
    const plan = planInvestigation({ title: "Budget variance review", templateId: "budget_audit" });
    const findings = buildFindings({
      questions: plan.questions.slice(0, 2),
      evidence: [{ id: "e1", kind: "budget", label: "variance 12%", excerpt: "12% over approved" }],
      conflicts: [],
      allowedCitationIds: [],
    });
    const recs = buildRecommendations(findings);
    const evidenceQuality = scoreEvidenceQuality({
      evidence: [{ id: "e1", kind: "budget", label: "variance 12%", excerpt: "12% over approved" }],
      queryText: "budget variance",
    });
    const missing = detectMissingEvidence({
      strategy,
      evidence: [],
      evidenceNeeded: plan.evidenceNeeded,
      timelineLines: [],
    });
    const hyps = buildCompetingHypotheses({
      title: plan.goal,
      questions: plan.questions,
      strategy,
      evidence: [{ id: "e1", kind: "budget", label: "variance 12%", excerpt: "12% over" }],
      conflicts: [],
      missingEvidence: missing.items.map((m) => m.label),
    });
    const confidence = buildConfidenceBundle({
      findings,
      recommendations: recs,
      evidenceQuality,
      hypotheses: hyps,
      missing,
      conflicts: [],
    });
    assert.ok(confidence.findingConfidence);
    assert.ok(confidence.evidenceConfidence);
    assert.ok(confidence.overallReadiness);

    const review = buildReviewChecklist({
      plan,
      findings,
      recommendations: recs,
      conflicts: [],
      missing,
      hypotheses: hyps,
      confidence,
      allowedCitationIds: [],
      reportCitations: [],
    });
    assert.equal(review.requiredStatus, "review");
    assert.ok(review.checks.length >= 6);

    const metrics = buildInvestigationMetrics({
      startedAt: 1000,
      completedAt: 2500,
      documentsReviewed: 1,
      evidenceQuality,
      citationCoverage: 0,
      hypotheses: hyps,
      conflicts: [],
      findings,
      confidence,
    });
    assert.equal(metrics.durationMs, 1500);
    assert.ok(metrics.hypothesesGenerated >= 2);

    const sections = buildReportSections({
      title: plan.goal,
      plan,
      evidenceLabels: ["variance 12%"],
      timelineLines: [],
      findings,
      conflicts: [],
      recommendations: recs,
      allowedCitationIds: [],
      hypotheses: hyps,
      missing,
      confidence,
      review,
      metrics,
      evidenceQuality,
    });
    const md = renderMarkdownReport(plan.goal, sections);
    assert.match(md, /Missing Evidence/);
    assert.match(md, /Competing Hypotheses/);
    assert.match(md, /Confidence Summary/);
    assert.match(md, /Methodology/);
    assert.match(md, /Known Limitations/);
  });

  it("rejects invented citations in review", () => {
    const plan = planInvestigation({ title: "Policy gap", templateId: "policy_review" });
    const findings = buildFindings({
      questions: ["What policy?"],
      evidence: [],
      conflicts: [],
      allowedCitationIds: ["cite_ok"],
    });
    const hyps = [
      {
        id: "h1",
        title: "A",
        summary: "s",
        supportingEvidence: [],
        contradictingEvidence: [],
        confidence: "insufficient_evidence" as const,
        missingEvidence: [],
        status: "unsupported" as const,
      },
      {
        id: "h2",
        title: "B",
        summary: "s",
        supportingEvidence: [],
        contradictingEvidence: [],
        confidence: "insufficient_evidence" as const,
        missingEvidence: [],
        status: "unsupported" as const,
      },
    ];
    const confidence = buildConfidenceBundle({
      findings,
      recommendations: [],
      evidenceQuality: scoreEvidenceQuality({ evidence: [] }),
      hypotheses: hyps,
      missing: { items: [], evidenceNeededSection: [] },
      conflicts: [],
    });
    const review = buildReviewChecklist({
      plan,
      findings,
      recommendations: [],
      conflicts: [],
      missing: { items: [], evidenceNeededSection: [] },
      hypotheses: hyps,
      confidence,
      allowedCitationIds: ["cite_ok"],
      reportCitations: ["cite_ok", "cite_FORGED"],
    });
    assert.equal(review.checks.find((c) => c.id === "citations_valid")?.passed, false);
    assert.equal(review.publicationAllowed, false);
  });
});

