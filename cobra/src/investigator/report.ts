import type {
  FindingDraft,
  InvestigationPlan,
  RecommendationDraft,
  ReportSections,
} from "./types.js";

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
}): ReportSections {
  const citations = [
    ...new Set([
      ...input.allowedCitationIds,
      ...input.findings.flatMap((f) => f.citations),
    ]),
  ];

  const execBits: string[] = [];
  execBits.push(`Investigation: ${input.title}.`);
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
  execBits.push("All factual claims in this report are limited to cited or inventoried evidence.");

  return {
    executiveSummary: execBits.join(" "),
    scope: input.description?.trim() || input.plan.goal,
    questions: input.plan.questions,
    evidenceReviewed: input.evidenceLabels,
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
    appendix: [
      `Template: ${input.plan.templateId ?? "none"}`,
      `Assumptions: ${input.plan.assumptions.join("; ")}`,
      `Deliverables: ${input.plan.deliverables.join(", ")}`,
    ],
    citations,
  };
}

export function renderMarkdownReport(
  title: string,
  sections: ReportSections,
): string {
  const lines: string[] = [
    `# ${title}`,
    "",
    "## Executive Summary",
    sections.executiveSummary,
    "",
    "## Investigation Scope",
    sections.scope,
    "",
    "## Questions",
    ...sections.questions.map((q, i) => `${i + 1}. ${q}`),
    "",
    "## Evidence Reviewed",
    ...sections.evidenceReviewed.map((e) => `- ${e}`),
    "",
    "## Timeline",
    ...sections.timeline.map((t) => `- ${t}`),
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
