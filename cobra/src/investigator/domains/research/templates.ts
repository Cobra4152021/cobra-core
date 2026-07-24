/** Research investigation templates (KC-009) — 9 templates, deterministic. */

import type { ResearchEvidenceCategoryId } from "./taxonomy.js";

export type ResearchTemplateId =
  | "research_literature_review"
  | "research_evidence_synthesis"
  | "research_historical_investigation"
  | "research_environmental_study"
  | "research_technical_root_cause"
  | "research_intelligence_assessment"
  | "research_case_study"
  | "research_field_investigation"
  | "research_anomaly_investigation";

export interface ResearchTemplate {
  id: ResearchTemplateId;
  version: string;
  title: string;
  objective: string;
  defaultQuestions: string[];
  defaultHypotheses: string[];
  requiredEvidenceCategories: ResearchEvidenceCategoryId[];
  optionalEvidenceCategories: ResearchEvidenceCategoryId[];
  strategyId: string;
  evidenceNeeded: string[];
  deliverables: string[];
  exclusions: string[];
  riskLevel: "low" | "medium" | "high" | "critical";
}

function t(
  partial: Omit<ResearchTemplate, "version" | "evidenceNeeded"> & {
    version?: string;
    evidenceNeeded?: string[];
  },
): ResearchTemplate {
  const evidenceNeeded =
    partial.evidenceNeeded ??
    [
      ...partial.requiredEvidenceCategories.map((c) => c.replace(/_/g, " ")),
      ...partial.optionalEvidenceCategories.slice(0, 3).map((c) => c.replace(/_/g, " ")),
    ];
  return { version: "0.1.0", ...partial, evidenceNeeded };
}

export const RESEARCH_TEMPLATES: ResearchTemplate[] = [
  t({
    id: "research_literature_review",
    title: "Literature Review",
    objective: "Survey and synthesize published literature on a research question without claiming peer review.",
    defaultQuestions: [
      "What is the precise research question?",
      "Which databases and date ranges were searched?",
      "What inclusion and exclusion criteria apply?",
      "What gaps remain in the literature?",
    ],
    defaultHypotheses: [
      "Literature converges on a dominant explanation.",
      "Literature presents competing explanations with comparable support.",
      "Evidence is sparse or methodologically inconsistent.",
    ],
    requiredEvidenceCategories: ["peer_reviewed_paper"],
    optionalEvidenceCategories: ["book", "government_report", "secondary_source"],
    strategyId: "research_investigation",
    deliverables: ["source inventory", "synthesis matrix", "gaps list", "research report"],
    exclusions: ["Not a systematic review certification.", "Not publication-ready without human review."],
    riskLevel: "medium",
  }),
  t({
    id: "research_evidence_synthesis",
    title: "Evidence Synthesis",
    objective: "Integrate heterogeneous sources into a structured evidence matrix with competing explanations.",
    defaultQuestions: [
      "Which claims require corroboration?",
      "Where do sources agree or conflict?",
      "What evidence is missing or low reliability?",
    ],
    defaultHypotheses: [
      "Available evidence supports a primary explanation.",
      "Evidence is mixed; no dominant explanation.",
      "Insufficient evidence for confident synthesis.",
    ],
    requiredEvidenceCategories: ["primary_source"],
    optionalEvidenceCategories: ["peer_reviewed_paper", "government_report", "secondary_source", "field_observation"],
    strategyId: "evidence_review",
    deliverables: ["evidence matrix", "hypothesis workspace", "confidence summary"],
    exclusions: ["Not a legal or regulatory finding."],
    riskLevel: "high",
  }),
  t({
    id: "research_historical_investigation",
    title: "Historical Investigation",
    objective: "Reconstruct events and context from archival and historical sources with explicit uncertainty.",
    defaultQuestions: [
      "What time period and actors are in scope?",
      "Which primary and secondary sources exist?",
      "Where do accounts conflict?",
    ],
    defaultHypotheses: [
      "Primary sources support a coherent timeline.",
      "Secondary accounts conflict with primary records.",
      "Key archival gaps prevent reconstruction.",
    ],
    requiredEvidenceCategories: ["primary_source"],
    optionalEvidenceCategories: ["secondary_source", "book", "newspaper", "government_report"],
    strategyId: "research_investigation",
    deliverables: ["timeline", "source reliability notes", "competing narratives"],
    exclusions: ["Not a definitive historical adjudication."],
    riskLevel: "medium",
  }),
  t({
    id: "research_environmental_study",
    title: "Environmental Study",
    objective: "Analyze environmental and geographic correlations using documented observations and sensor data.",
    defaultQuestions: [
      "What environmental variables are measured?",
      "What sampling methods and instruments were used?",
      "Are there confounding geographic or temporal factors?",
    ],
    defaultHypotheses: [
      "Environmental data supports the proposed correlation.",
      "Confounders explain the observed pattern.",
      "Data quality or coverage is insufficient.",
    ],
    requiredEvidenceCategories: ["environmental"],
    optionalEvidenceCategories: ["geographic", "field_observation", "government_report", "peer_reviewed_paper"],
    strategyId: "research_investigation",
    deliverables: ["environmental summary", "geographic overlay notes", "limitations"],
    exclusions: ["Not an environmental compliance determination."],
    riskLevel: "high",
  }),
  t({
    id: "research_technical_root_cause",
    title: "Technical Root Cause Analysis",
    objective: "Investigate technical failures or anomalies using reproducible evidence and competing causal hypotheses.",
    defaultQuestions: [
      "What failure mode or anomaly is observed?",
      "What logs, experiments, or primary data exist?",
      "Which hypotheses remain untested?",
    ],
    defaultHypotheses: [
      "A single root cause explains the failure.",
      "Multiple contributing factors jointly explain the failure.",
      "Insufficient data to isolate root cause.",
    ],
    requiredEvidenceCategories: ["primary_source"],
    optionalEvidenceCategories: ["peer_reviewed_paper", "field_observation", "government_report"],
    strategyId: "technical_root_cause",
    deliverables: ["causal hypothesis matrix", "reproducibility notes", "findings"],
    exclusions: ["Not a warranty or liability determination."],
    riskLevel: "high",
  }),
  t({
    id: "research_intelligence_assessment",
    title: "Intelligence Assessment",
    objective: "Assess claims from mixed sources with explicit reliability scoring and confidence levels.",
    defaultQuestions: [
      "What is the intelligence question?",
      "Which sources are primary versus derivative?",
      "Where is corroboration weak or absent?",
    ],
    defaultHypotheses: [
      "Corroborated sources support the assessment.",
      "Single-source or anonymous claims dominate; confidence is low.",
      "Deception or bias may affect key sources.",
    ],
    requiredEvidenceCategories: ["primary_source"],
    optionalEvidenceCategories: ["anonymous_source", "expert_testimony", "government_report", "internet_article"],
    strategyId: "evidence_review",
    deliverables: ["source reliability scores", "assessment summary", "information gaps"],
    exclusions: ["Not an operational or policy directive."],
    riskLevel: "critical",
  }),
  t({
    id: "research_case_study",
    title: "Case Study",
    objective: "Document a bounded case with evidence, timeline, and lessons learned without overgeneralizing.",
    defaultQuestions: [
      "What are the case boundaries?",
      "What evidence supports each finding?",
      "What limitations apply to generalization?",
    ],
    defaultHypotheses: [
      "Case evidence supports documented findings.",
      "Alternative explanations remain plausible.",
      "Case records are incomplete.",
    ],
    requiredEvidenceCategories: ["primary_source"],
    optionalEvidenceCategories: ["secondary_source", "field_observation", "expert_testimony"],
    strategyId: "general_investigation",
    deliverables: ["case narrative", "evidence inventory", "lessons learned"],
    exclusions: ["Not a population-level statistical claim."],
    riskLevel: "medium",
  }),
  t({
    id: "research_field_investigation",
    title: "Field Investigation",
    objective: "Organize field observations, interviews, and site evidence into a structured investigation record.",
    defaultQuestions: [
      "What sites or subjects were observed?",
      "What instruments and protocols were used?",
      "What chain-of-custody applies to collected evidence?",
    ],
    defaultHypotheses: [
      "Field observations align with documented expectations.",
      "Unexpected observations require additional investigation.",
      "Observation conditions limit reliability.",
    ],
    requiredEvidenceCategories: ["field_observation"],
    optionalEvidenceCategories: ["geographic", "environmental", "audio", "expert_testimony", "primary_source"],
    strategyId: "research_investigation",
    deliverables: ["field log", "site timeline", "observation matrix"],
    exclusions: ["Not a forensic certification."],
    riskLevel: "high",
  }),
  t({
    id: "research_anomaly_investigation",
    title: "Anomaly Investigation",
    objective:
      "Long-form anomaly investigation with sighting timeline, geographic and environmental correlations, audio evidence, competing explanations, and confidence scoring.",
    defaultQuestions: [
      "What anomaly events occurred and when?",
      "What geographic and environmental context applies?",
      "What audio or sensor captures exist?",
      "What prosaic and non-prosaic explanations compete?",
      "What evidence would change confidence?",
    ],
    defaultHypotheses: [
      "Observations are explained by known natural or human causes.",
      "Observations suggest an unidentified phenomenon requiring further study.",
      "Evidence quality or quantity prevents confident explanation.",
      "Multiple independent observations support a pattern beyond single-witness error.",
    ],
    requiredEvidenceCategories: ["field_observation"],
    optionalEvidenceCategories: ["geographic", "environmental", "audio", "primary_source", "anonymous_source", "newspaper"],
    strategyId: "research_investigation",
    deliverables: ["sighting timeline", "correlation map notes", "competing explanations", "confidence summary"],
    exclusions: ["Not a scientific peer-review conclusion.", "Not proof of extraordinary claims."],
    riskLevel: "high",
  }),
];

export function listResearchTemplates(): ResearchTemplate[] {
  return RESEARCH_TEMPLATES.map((x) => ({ ...x }));
}

export function getResearchTemplate(id: string | null | undefined): ResearchTemplate | null {
  if (!id) return null;
  return RESEARCH_TEMPLATES.find((x) => x.id === id) ?? null;
}

export function isResearchTemplateId(id: string | null | undefined): id is ResearchTemplateId {
  return Boolean(id && RESEARCH_TEMPLATES.some((x) => x.id === id));
}
