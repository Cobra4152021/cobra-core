import type {
  FindingDraft,
  InvestigationPlan,
  RecommendationDraft,
  ReportSections,
} from "./types.js";
import type { HypothesisDraft } from "./hypotheses.js";
import type { MissingEvidenceReport } from "./missingEvidence.js";
import type { ConfidenceBundle } from "./confidence.js";
import type { ReviewChecklist } from "./review.js";
import type { InvestigationMetrics } from "./metrics.js";
import type { EvidenceQualitySummary } from "./evidenceQuality.js";

export function buildReportSections(input: {
  title: string;
  description?: string | null;
  plan: InvestigationPlan;
  evidenceLabels: string[];
  timelineLines: string[];
  findings: FindingDraft[];
  conflicts: string[];
  recommendations: RecommendationDraft[];
  allowedCitationIds: string[];
  hypotheses?: HypothesisDraft[];
  missing?: MissingEvidenceReport;
  confidence?: ConfidenceBundle;
  review?: ReviewChecklist;
  metrics?: InvestigationMetrics;
  evidenceQuality?: EvidenceQualitySummary;
}): ReportSections {
  const citations = [
    ...new Set([
      ...input.allowedCitationIds,
      ...input.findings.flatMap((f) => f.citations),
    ]),
  ];

  const execBits: string[] = [];
  execBits.push(`Investigation: ${input.title}.`);
  if (input.plan.strategyName) {
    execBits.push(`Strategy: ${input.plan.strategyName}.`);
  }
  if (input.findings.some((f) => f.confidence === "insufficient_evidence")) {
    execBits.push("Several questions remain unsupported by accessible evidence.");
  }
  const highs = input.findings.filter((f) => f.confidence === "high");
  if (highs.length) {
    execBits.push(`${highs.length} high-confidence finding(s) were identified.`);
  }
  if (input.conflicts.length) {
    execBits.push(`${input.conflicts.length} conflict(s) were preserved for review.`);
  }
  if (input.hypotheses?.length) {
    execBits.push(`${input.hypotheses.length} competing hypothesis(es) remain under consideration.`);
  }
  if (input.confidence) {
    execBits.push(
      `Investigation confidence: ${input.confidence.investigationConfidence}; readiness: ${input.confidence.overallReadiness}.`,
    );
  }
  execBits.push("All factual claims in this report are limited to cited or inventoried evidence.");

  const knownLimitations = [
    "Retrieval is limited to organization-scoped Knowledge Engine and Evidence Vault content.",
    "Evidence quality scores are deterministic heuristics, not human authenticity judgments.",
    ...(input.missing?.items.slice(0, 5).map((m) => `Missing: ${m.label}`) ?? []),
    ...(input.plan.confidenceRules ?? []),
  ];

  const competingHypotheses =
    input.hypotheses?.map(
      (h) =>
        `[${h.status}/${h.confidence}] ${h.title}: ${h.summary}` +
        (h.supportingEvidence.length
          ? ` Support: ${h.supportingEvidence.slice(0, 4).join(", ")}`
          : " Support: none") +
        (h.missingEvidence.length
          ? ` Missing: ${h.missingEvidence.slice(0, 3).join(", ")}`
          : ""),
    ) ?? ["No competing hypotheses generated."];

  const confidenceSummary = input.confidence
    ? [
        `Finding confidence: ${input.confidence.findingConfidence}`,
        `Evidence confidence: ${input.confidence.evidenceConfidence}`,
        `Recommendation confidence: ${input.confidence.recommendationConfidence}`,
        `Investigation confidence: ${input.confidence.investigationConfidence}`,
        `Overall readiness: ${input.confidence.overallReadiness}`,
        ...input.confidence.rationale,
        ...(input.evidenceQuality
          ? [
              `Evidence quality mean/median: ${input.evidenceQuality.meanOverall}/${input.evidenceQuality.medianOverall}`,
            ]
          : []),
        ...(input.review
          ? [
              `Review checklist: ${input.review.passedCount} passed / ${input.review.failedCount} failed — ${input.review.summary}`,
            ]
          : []),
        ...(input.metrics
          ? [
              `Duration: ${input.metrics.durationMs}ms; documents reviewed: ${input.metrics.documentsReviewed}; citation coverage: ${input.metrics.citationCoverage}`,
            ]
          : []),
      ]
    : ["Confidence summary unavailable."];

  return {
    executiveSummary: execBits.join(" "),
    scope: input.description?.trim() || input.plan.goal,
    methodology: input.plan.methodology ?? ["Deterministic investigation pipeline"],
    knownLimitations,
    questions: input.plan.questions,
    evidenceReviewed: input.evidenceLabels,
    missingEvidence: input.missing?.evidenceNeededSection ?? ["No missing-evidence analysis."],
    competingHypotheses,
    timeline: input.timelineLines,
    findings: input.findings.map(
      (f) =>
        `[${f.confidence}] ${f.title}: ${f.summary}` +
        (f.citations.length ? ` Citations: ${f.citations.join(", ")}` : " (no citations)"),
    ),
    conflicts: input.conflicts.length ? input.conflicts : ["No open conflicts recorded."],
    recommendations: input.recommendations.map(
      (r) => `[${r.priority}/${r.confidence}] ${r.title}: ${r.body}`,
    ),
    confidenceSummary,
    appendix: [
      `Template: ${input.plan.templateId ?? "none"}`,
      `Strategy: ${input.plan.strategyId ?? "none"} (${input.plan.strategyName ?? ""})`,
      `Assumptions: ${input.plan.assumptions.join("; ")}`,
      `Deliverables: ${input.plan.deliverables.join(", ")}`,
      ...(input.review?.checks.map((c) => `Review[${c.passed ? "pass" : "fail"}] ${c.id}: ${c.detail}`) ??
        []),
    ],
    citations,
  };
}

export function renderMarkdownReport(title: string, sections: ReportSections): string {
  const lines: string[] = [
    `# ${title}`,
    "",
    "## Executive Summary",
    sections.executiveSummary,
    "",
    "## Scope",
    sections.scope,
    "",
    "## Methodology",
    ...sections.methodology.map((m) => `- ${m}`),
    "",
    "## Known Limitations",
    ...sections.knownLimitations.map((m) => `- ${m}`),
    "",
    "## Questions",
    ...sections.questions.map((q, i) => `${i + 1}. ${q}`),
    "",
    "## Evidence Reviewed",
    ...(sections.evidenceReviewed.length
      ? sections.evidenceReviewed.map((e) => `- ${e}`)
      : ["- (none retrieved)"]),
    "",
    "## Missing Evidence",
    ...sections.missingEvidence.map((m) => `- ${m}`),
    "",
    "## Competing Hypotheses",
    ...sections.competingHypotheses.map((h) => `- ${h}`),
    "",
    "## Timeline",
    ...(sections.timeline.length ? sections.timeline.map((t) => `- ${t}`) : ["- (none)"]),
    "",
    "## Findings",
    ...sections.findings.map((f) => `- ${f}`),
    "",
    "## Conflicts",
    ...sections.conflicts.map((c) => `- ${c}`),
    "",
    "## Recommendations",
    ...sections.recommendations.map((r) => `- ${r}`),
    "",
    "## Confidence Summary",
    ...sections.confidenceSummary.map((c) => `- ${c}`),
    "",
    "## Appendix",
    ...sections.appendix.map((a) => `- ${a}`),
    "",
    "## Citations",
    ...(sections.citations.length
      ? sections.citations.map((c) => `- ${c}`)
      : ["- (none — evidence was not found or citations unavailable)"]),
    "",
  ];
  return lines.join("\n");
}
