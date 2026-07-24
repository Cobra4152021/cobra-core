/** Built-in investigation templates (KC-004). */

export type TemplateId =
  | "government_audit"
  | "union_audit"
  | "budget_audit"
  | "policy_review"
  | "compliance_review"
  | "technical_audit"
  | "research_investigation"
  | "evidence_review"
  | "security_review";

export interface InvestigationTemplate {
  id: TemplateId;
  name: string;
  defaultQuestions: string[];
  evidenceNeeded: string[];
  deliverables: string[];
}

export const INVESTIGATION_TEMPLATES: InvestigationTemplate[] = [
  {
    id: "government_audit",
    name: "Government Audit",
    defaultQuestions: [
      "What policy or statute governs this area?",
      "What spending or staffing changes occurred?",
      "Are reported figures consistent across sources?",
      "What decisions authorized the change?",
    ],
    evidenceNeeded: ["policy documents", "budget tables", "decision records", "timelines"],
    deliverables: ["findings", "conflicts", "recommendations", "executive summary"],
  },
  {
    id: "union_audit",
    name: "Union Audit",
    defaultQuestions: [
      "What contractual obligations apply?",
      "Were staffing levels consistent with the agreement?",
      "Is overtime usage consistent with vacancy and workload data?",
    ],
    evidenceNeeded: ["collective agreement", "staffing records", "overtime logs", "grievances"],
    deliverables: ["findings", "timeline", "recommendations"],
  },
  {
    id: "budget_audit",
    name: "Budget Audit",
    defaultQuestions: [
      "What was budgeted versus actual?",
      "Which line items drove the variance?",
      "Were transfers or supplements authorized?",
    ],
    evidenceNeeded: ["budgets", "actuals", "transfer memos", "decisions"],
    deliverables: ["variance findings", "recommendations"],
  },
  {
    id: "policy_review",
    name: "Policy Review",
    defaultQuestions: [
      "What does the current policy require?",
      "Where does practice diverge from policy?",
      "What conflicts exist between policies?",
    ],
    evidenceNeeded: ["policies", "procedures", "practice evidence"],
    deliverables: ["gap analysis", "recommendations"],
  },
  {
    id: "compliance_review",
    name: "Compliance Review",
    defaultQuestions: [
      "Which requirements apply?",
      "What evidence demonstrates compliance?",
      "Where is evidence missing?",
    ],
    evidenceNeeded: ["requirements", "controls evidence", "exceptions"],
    deliverables: ["compliance matrix", "findings"],
  },
  {
    id: "technical_audit",
    name: "Technical Audit",
    defaultQuestions: [
      "What system or process changed?",
      "What failures or defects were observed?",
      "What mitigations were applied?",
    ],
    evidenceNeeded: ["logs", "change records", "incident reports"],
    deliverables: ["root-cause findings", "recommendations"],
  },
  {
    id: "research_investigation",
    name: "Research Investigation",
    defaultQuestions: [
      "What is the research question?",
      "What sources are authoritative?",
      "Where do sources disagree?",
    ],
    evidenceNeeded: ["primary sources", "secondary analyses", "timelines"],
    deliverables: ["findings", "conflicts", "citation appendix"],
  },
  {
    id: "evidence_review",
    name: "Evidence Review",
    defaultQuestions: [
      "What evidence is available?",
      "What is missing or inaccessible?",
      "What does the evidence support or refute?",
    ],
    evidenceNeeded: ["vault documents", "citations", "extractions"],
    deliverables: ["evidence inventory", "gaps", "findings"],
  },
  {
    id: "security_review",
    name: "Security Review",
    defaultQuestions: [
      "What assets and threats are in scope?",
      "What controls exist?",
      "What residual risks remain?",
    ],
    evidenceNeeded: ["asset inventory", "control evidence", "incident history"],
    deliverables: ["risk findings", "recommendations"],
  },
];

export function getTemplate(id: string | null | undefined): InvestigationTemplate | null {
  if (!id) return null;
  return INVESTIGATION_TEMPLATES.find((t) => t.id === id) ?? null;
}
