/** Labor investigation report overlay (KC-006). */

import { LABOR_DISCLAIMERS, LABOR_DEFAULT_REPORT_SECTIONS } from "./domain.js";
import type { LaborTemplate } from "./templates.js";

export interface LaborReportSection {
  id: string;
  title: string;
  body: string;
}

const TITLES: Record<string, string> = {
  executive_summary: "Executive Summary",
  scope: "Scope",
  contract_articles_reviewed: "Contract Articles Reviewed",
  timeline: "Timeline",
  evidence: "Evidence",
  supporting_evidence: "Supporting Evidence",
  contrary_evidence: "Contrary Evidence",
  missing_evidence: "Missing Evidence",
  findings: "Findings",
  recommendations: "Recommendations",
  confidence: "Confidence",
  appendix: "Appendix",
  citations: "Citations",
};

export function buildLaborReportSections(input: {
  title: string;
  template: LaborTemplate;
  scope?: string;
  articles?: string[];
  timeline?: string[];
  evidence?: string[];
  supporting?: string[];
  contrary?: string[];
  missing?: string[];
  findings?: string[];
  recommendations?: string[];
  confidence?: string;
  citations?: string[];
  appendix?: string;
}): LaborReportSection[] {
  const disclaimer = LABOR_DISCLAIMERS.map((d) => `- ${d}`).join("\n");
  const bodies: Record<string, string> = {
    executive_summary:
      "Neutral summary of scope, articles reviewed, competing explanations, and open evidence gaps. No legal conclusions.",
    scope: input.scope ?? input.template.objective,
    contract_articles_reviewed:
      (input.articles ?? []).map((a) => `- ${a}`).join("\n") || "- None listed.",
    timeline: (input.timeline ?? []).map((t) => `- ${t}`).join("\n") || "- Timeline pending.",
    evidence: (input.evidence ?? []).map((e) => `- ${e}`).join("\n") || "- Evidence inventory pending.",
    supporting_evidence:
      (input.supporting ?? []).map((e) => `- ${e}`).join("\n") || "- None recorded.",
    contrary_evidence: (input.contrary ?? []).map((e) => `- ${e}`).join("\n") || "- None recorded.",
    missing_evidence: (input.missing ?? []).map((e) => `- ${e}`).join("\n") || "- None listed.",
    findings:
      (input.findings ?? []).map((f) => `- ${f}`).join("\n") ||
      "- Findings pending evidence-backed analysis.",
    recommendations:
      (input.recommendations ?? []).map((r) => `- ${r}`).join("\n") ||
      "- Recommendations pending human review.",
    confidence:
      (input.confidence ??
        "Confidence depends on completeness of records. Human review required.") +
      `\n\nNotices:\n${disclaimer}`,
    appendix: input.appendix ?? "Supporting matrices, exhibit indexes, and request lists.",
    citations: (input.citations ?? []).map((c) => `- ${c}`).join("\n") || "- No citations yet.",
  };

  return LABOR_DEFAULT_REPORT_SECTIONS.map((id) => ({
    id,
    title: TITLES[id] ?? id,
    body: bodies[id] ?? "",
  }));
}

export function renderLaborMarkdownReport(sections: LaborReportSection[]): string {
  return sections.map((s) => `## ${s.title}\n\n${s.body}\n`).join("\n");
}
