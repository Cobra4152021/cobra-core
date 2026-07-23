/** Government Investigation Report format overlay (KC-005). */

import { GOVERNMENT_DISCLAIMERS, GOVERNMENT_DEFAULT_REPORT_SECTIONS } from "./domain.js";
import type { GovernmentMetric } from "./metrics.js";
import type { GovernmentTemplate } from "./templates.js";

export interface GovernmentReportSection {
  id: string;
  title: string;
  body: string;
}

export function governmentReportSectionTitles(): { id: string; title: string }[] {
  const titles: Record<string, string> = {
    cover: "Cover",
    executive_summary: "Executive Summary",
    authority_and_purpose: "Authority and Purpose",
    investigation_objective: "Investigation Objective",
    scope: "Scope",
    methodology: "Methodology",
    evidence_reviewed: "Evidence Reviewed",
    data_limitations: "Data Limitations",
    background: "Background",
    timeline: "Timeline",
    metrics_and_trends: "Metrics and Trends",
    competing_hypotheses: "Competing Hypotheses",
    findings: "Findings",
    contrary_or_mitigating_evidence: "Contrary or Mitigating Evidence",
    missing_evidence: "Missing Evidence",
    recommendations: "Recommendations",
    management_questions: "Management Questions",
    confidence_and_readiness: "Confidence and Readiness",
    appendix: "Appendix",
    citations: "Citations",
    report_version_and_audit_metadata: "Report Version and Audit Metadata",
  };
  return GOVERNMENT_DEFAULT_REPORT_SECTIONS.map((id) => ({
    id,
    title: titles[id] ?? id,
  }));
}

export function buildGovernmentReportSections(input: {
  title: string;
  template: GovernmentTemplate;
  objective?: string;
  scope?: string;
  methodology?: string[];
  evidenceLabels?: string[];
  limitations?: string[];
  background?: string;
  timelineNotes?: string[];
  metrics?: GovernmentMetric[];
  hypotheses?: string[];
  findings?: string[];
  contrary?: string[];
  missing?: string[];
  recommendations?: string[];
  managementQuestions?: string[];
  confidenceSummary?: string;
  citations?: string[];
  version?: string;
  auditMeta?: string;
}): GovernmentReportSection[] {
  const metricLines =
    (input.metrics ?? [])
      .map((m) => {
        const val = m.value === null ? "insufficient data" : String(m.value);
        return `- ${m.name}: ${val} ${m.units} (${m.confidence}; formula: ${m.formula})`;
      })
      .join("\n") || "- No metrics calculated (missing source fields).";

  const disclaimerBlock = GOVERNMENT_DISCLAIMERS.map((d) => `- ${d}`).join("\n");

  const bodies: Record<string, string> = {
    cover: `# ${input.title}\n\nCobra Government Investigation Report\nTemplate: ${input.template.title} (${input.template.id} v${input.template.version})\n`,
    executive_summary:
      "Neutral summary of scope, primary findings, competing explanations, and open evidence gaps. No legal conclusions.",
    authority_and_purpose:
      "This report supports organizational fact-finding. It is investigative support, not an audit opinion or legal determination.",
    investigation_objective: input.objective ?? input.template.objective,
    scope: input.scope ?? input.template.scopePrompts.join("\n"),
    methodology: (input.methodology ?? ["Deterministic Government template planning", "CKE/Evidence Vault retrieval with citations", "Competing hypotheses retained"]).map((m) => `- ${m}`).join("\n"),
    evidence_reviewed: (input.evidenceLabels ?? []).map((e) => `- ${e}`).join("\n") || "- Evidence inventory pending.",
    data_limitations:
      (input.limitations ?? input.template.knownLimitations).map((l) => `- ${l}`).join("\n") +
      `\n\nNotices:\n${disclaimerBlock}`,
    background: input.background ?? "Background to be completed from authorized records.",
    timeline: (input.timelineNotes ?? []).map((t) => `- ${t}`).join("\n") || "- Timeline events pending evidence.",
    metrics_and_trends: metricLines,
    competing_hypotheses: (input.hypotheses ?? input.template.defaultHypotheses)
      .map((h) => `- ${h}`)
      .join("\n"),
    findings: (input.findings ?? []).map((f) => `- ${f}`).join("\n") || "- Findings pending evidence-backed analysis.",
    contrary_or_mitigating_evidence:
      (input.contrary ?? []).map((c) => `- ${c}`).join("\n") || "- No contrary evidence recorded yet.",
    missing_evidence: (input.missing ?? []).map((m) => `- ${m}`).join("\n") || "- None listed.",
    recommendations:
      (input.recommendations ?? []).map((r) => `- ${r}`).join("\n") ||
      "- Recommendations pending findings.",
    management_questions:
      (input.managementQuestions ?? input.template.defaultQuestions.slice(0, 5))
        .map((q) => `- ${q}`)
        .join("\n"),
    confidence_and_readiness:
      input.confidenceSummary ??
      "Confidence depends on completeness of records. Human review required before publication.",
    appendix: "Supporting tables, metric worksheets, and evidence request status.",
    citations: (input.citations ?? []).map((c) => `- ${c}`).join("\n") || "- No citations yet.",
    report_version_and_audit_metadata: `Version: ${input.version ?? "0.1.0-draft"}\n${input.auditMeta ?? "Audit metadata recorded in inv_audit_events."}`,
  };

  return governmentReportSectionTitles().map((s) => ({
    id: s.id,
    title: s.title,
    body: bodies[s.id] ?? "",
  }));
}

export function renderGovernmentMarkdownReport(sections: GovernmentReportSection[]): string {
  return sections.map((s) => `## ${s.title}\n\n${s.body}\n`).join("\n");
}
