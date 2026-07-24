/** Research investigation report (KC-009). */

import { RESEARCH_DISCLAIMERS } from "./domain.js";
import type { ResearchTemplate } from "./templates.js";

export const RESEARCH_DEFAULT_REPORT_SECTIONS = [
  "executive_summary",
  "background",
  "methodology",
  "evidence_matrix",
  "competing_hypotheses",
  "findings",
  "limitations",
  "future_research",
  "citations",
] as const;

export interface ResearchReportSection {
  id: string;
  title: string;
  body: string;
}

const TITLES: Record<string, string> = {
  executive_summary: "Executive Summary",
  background: "Background",
  methodology: "Methodology",
  evidence_matrix: "Evidence Matrix",
  competing_hypotheses: "Competing Hypotheses",
  findings: "Findings",
  limitations: "Limitations",
  future_research: "Future Research",
  citations: "Citations",
};

export function buildResearchReportSections(input: {
  title: string;
  template: ResearchTemplate;
  background?: string;
  methodology?: string;
  evidenceMatrix?: string;
  hypotheses?: string[];
  findings?: string[];
  limitations?: string[];
  futureResearch?: string[];
  citations?: string[];
}): ResearchReportSection[] {
  const disclaimer = RESEARCH_DISCLAIMERS.map((d) => `- ${d}`).join("\n");
  const bodies: Record<string, string> = {
    executive_summary:
      "Neutral summary of scope, key evidence, competing explanations, and confidence. No peer-review or legal conclusions.\n\n" +
      `Disclaimers:\n${disclaimer}`,
    background: input.background ?? input.template.objective,
    methodology:
      input.methodology ??
      "Structured evidence collection, reliability heuristics, matrix synthesis, and hypothesis tracking. Human review required.",
    evidence_matrix:
      input.evidenceMatrix ?? "Evidence matrix pending. Relations: supports, contradicts, neutral, uncertain, duplicate, outlier, missing.",
    competing_hypotheses:
      (input.hypotheses ?? input.template.defaultHypotheses).map((h) => `- ${h}`).join("\n") ||
      "- Competing hypotheses pending.",
    findings:
      (input.findings ?? []).map((f) => `- ${f}`).join("\n") ||
      "- Findings pending evidence-backed synthesis.",
    limitations:
      (input.limitations ?? []).map((l) => `- ${l}`).join("\n") ||
      "- Source gaps and heuristic reliability limits apply.",
    future_research:
      (input.futureResearch ?? []).map((r) => `- ${r}`).join("\n") ||
      "- Additional primary sources and reproducibility checks recommended.",
    citations: (input.citations ?? []).map((c) => `- ${c}`).join("\n") || "- No citations yet.",
  };

  return RESEARCH_DEFAULT_REPORT_SECTIONS.map((id) => ({
    id,
    title: TITLES[id] ?? id,
    body: bodies[id] ?? "",
  }));
}

export function renderResearchMarkdownReport(sections: ResearchReportSection[]): string {
  const header = RESEARCH_DISCLAIMERS.map((d) => `> ${d}`).join("\n");
  const body = sections.map((s) => `## ${s.title}\n\n${s.body}\n`).join("\n");
  return `${header}\n\n${body}`;
}
