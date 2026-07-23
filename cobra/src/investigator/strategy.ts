/**
 * Investigation Strategy Engine (KC-004B).
 * Selects an investigation strategy instead of a single generic plan.
 */

import type { Priority } from "./types.js";
import { getTemplate, type TemplateId } from "./templates.js";
import {
  getGovernmentTemplate,
  isGovernmentTemplateId,
} from "./domains/government/templates.js";
import {
  getLaborTemplate,
  isLaborTemplateId,
} from "./domains/labor/templates.js";

export type StrategyId =
  | "budget_audit"
  | "staffing_analysis"
  | "union_contract_review"
  | "compliance_investigation"
  | "research_investigation"
  | "technical_root_cause"
  | "security_investigation"
  | "policy_review"
  | "evidence_review"
  | "general_investigation";

export interface InvestigationStrategy {
  id: StrategyId;
  name: string;
  questions: string[];
  evidencePriorities: string[];
  confidenceRules: string[];
  expectedDeliverables: string[];
  templateId: TemplateId | null;
  defaultPriority: Priority;
}

const STRATEGIES: InvestigationStrategy[] = [
  {
    id: "budget_audit",
    name: "Budget Audit",
    questions: [
      "What was budgeted versus actual?",
      "Which line items drove the variance?",
      "Were transfers or supplements authorized?",
      "Do source documents agree on totals?",
    ],
    evidencePriorities: ["budgets", "actuals", "transfer memos", "decision records", "approvals"],
    confidenceRules: [
      "High confidence requires budget and actuals from authoritative sources.",
      "Variance claims without matching line-item evidence are low confidence.",
    ],
    expectedDeliverables: ["variance findings", "authorization gaps", "recommendations", "confidence summary"],
    templateId: "budget_audit",
    defaultPriority: "high",
  },
  {
    id: "staffing_analysis",
    name: "Staffing Analysis",
    questions: [
      "What headcount and vacancy rates applied?",
      "When did staffing changes occur?",
      "How did workload compare to capacity?",
      "How did overtime relate to vacancies?",
    ],
    evidencePriorities: ["staffing tables", "vacancy reports", "workload metrics", "overtime logs", "org charts"],
    confidenceRules: [
      "Staffing conclusions require contemporaneous headcount or vacancy evidence.",
      "Causal claims linking vacancies to overtime need corroborating time series.",
    ],
    expectedDeliverables: ["staffing timeline", "capacity findings", "recommendations"],
    templateId: null,
    defaultPriority: "medium",
  },
  {
    id: "union_contract_review",
    name: "Union Contract Review",
    questions: [
      "What contractual obligations apply?",
      "Were staffing levels consistent with the agreement?",
      "Is overtime usage consistent with vacancy and workload data?",
      "Were contractual or policy limits exceeded?",
    ],
    evidencePriorities: [
      "collective agreement",
      "staffing records",
      "overtime logs",
      "grievances",
      "payroll extracts",
    ],
    confidenceRules: [
      "Contractual findings require the agreement text or an authoritative summary.",
      "Overtime compliance claims need both contract limits and usage evidence.",
    ],
    expectedDeliverables: ["findings", "timeline", "recommendations", "missing evidence"],
    templateId: "union_audit",
    defaultPriority: "high",
  },
  {
    id: "compliance_investigation",
    name: "Compliance Investigation",
    questions: [
      "Which requirements apply?",
      "What evidence demonstrates compliance?",
      "Where is evidence missing?",
      "What exceptions were approved?",
    ],
    evidencePriorities: ["requirements", "controls evidence", "exceptions", "policies", "approvals"],
    confidenceRules: [
      "Compliance assertions need mapped requirement-to-evidence links.",
      "Missing required evidence caps readiness at Review Required.",
    ],
    expectedDeliverables: ["compliance matrix", "findings", "gaps"],
    templateId: "compliance_review",
    defaultPriority: "high",
  },
  {
    id: "research_investigation",
    name: "Research Investigation",
    questions: [
      "What is the research question?",
      "What sources are authoritative?",
      "Where do sources disagree?",
      "What remains unproven?",
    ],
    evidencePriorities: ["primary sources", "secondary analyses", "timelines", "citations"],
    confidenceRules: [
      "Primary sources outrank secondary commentary.",
      "Unresolved contradictions prevent high investigation confidence.",
    ],
    expectedDeliverables: ["findings", "conflicts", "citation appendix"],
    templateId: "research_investigation",
    defaultPriority: "medium",
  },
  {
    id: "technical_root_cause",
    name: "Technical Root Cause Analysis",
    questions: [
      "What system or process changed?",
      "What failures or defects were observed?",
      "What mitigations were applied?",
      "What is the most likely root cause versus alternatives?",
    ],
    evidencePriorities: ["logs", "change records", "incident reports", "monitoring", "timelines"],
    confidenceRules: [
      "Root-cause claims require temporal alignment of change and failure evidence.",
      "Competing technical hypotheses must remain visible until disconfirmed.",
    ],
    expectedDeliverables: ["root-cause findings", "hypotheses", "recommendations"],
    templateId: "technical_audit",
    defaultPriority: "high",
  },
  {
    id: "security_investigation",
    name: "Security Investigation",
    questions: [
      "What assets and threats are in scope?",
      "What controls exist?",
      "What residual risks remain?",
      "What evidence of compromise or misuse exists?",
    ],
    evidencePriorities: ["asset inventory", "control evidence", "incident history", "access logs"],
    confidenceRules: [
      "Security findings require control or incident evidence, not inference alone.",
      "Absence of evidence is not evidence of absence for high-impact risks.",
    ],
    expectedDeliverables: ["risk findings", "recommendations", "missing evidence"],
    templateId: "security_review",
    defaultPriority: "critical",
  },
  {
    id: "policy_review",
    name: "Policy Review",
    questions: [
      "What does the current policy require?",
      "Where does practice diverge from policy?",
      "What conflicts exist between policies?",
    ],
    evidencePriorities: ["policies", "procedures", "practice evidence", "exception approvals"],
    confidenceRules: [
      "Gap findings need both policy text and practice evidence.",
    ],
    expectedDeliverables: ["gap analysis", "recommendations"],
    templateId: "policy_review",
    defaultPriority: "medium",
  },
  {
    id: "evidence_review",
    name: "Evidence Review",
    questions: [
      "What evidence is available?",
      "What is missing or inaccessible?",
      "What does the evidence support or refute?",
    ],
    evidencePriorities: ["vault documents", "citations", "extractions", "indexes"],
    confidenceRules: [
      "Inventory completeness drives investigation readiness.",
    ],
    expectedDeliverables: ["evidence inventory", "gaps", "findings"],
    templateId: "evidence_review",
    defaultPriority: "medium",
  },
  {
    id: "general_investigation",
    name: "General Investigation",
    questions: [
      "What is the precise problem?",
      "What evidence is already available?",
      "What competing explanations should be tested?",
      "What timeline of decisions and events is relevant?",
    ],
    evidencePriorities: [
      "Knowledge Engine memories and facts",
      "Evidence Vault documents and citations",
      "Timeline events and decisions",
      "Recorded conflicts",
    ],
    confidenceRules: [
      "Unsupported claims must be marked insufficient evidence.",
      "Conflicts are preserved, not silently resolved.",
    ],
    expectedDeliverables: [
      "investigation plan",
      "evidence inventory",
      "findings",
      "recommendations",
      "citation-backed report",
    ],
    templateId: null,
    defaultPriority: "medium",
  },
];

const HINTS: { re: RegExp; strategyId: StrategyId }[] = [
  { re: /overtime|ot\b|union|collective\s*agreement|grievance/i, strategyId: "union_contract_review" },
  { re: /budget|spending|expenditure|variance|cost/i, strategyId: "budget_audit" },
  { re: /staff|vacanc|hiring|workforce|fte|headcount/i, strategyId: "staffing_analysis" },
  { re: /security|breach|threat|access\s*control|compromise/i, strategyId: "security_investigation" },
  { re: /root\s*cause|outage|defect|incident|failure|bug/i, strategyId: "technical_root_cause" },
  { re: /compliance|regulation|statutory|audit\b/i, strategyId: "compliance_investigation" },
  { re: /policy|procedure/i, strategyId: "policy_review" },
  { re: /research|literature|source\s*review/i, strategyId: "research_investigation" },
  { re: /evidence\s*review|inventory/i, strategyId: "evidence_review" },
];

export function listStrategies(): InvestigationStrategy[] {
  return STRATEGIES.map((s) => ({ ...s }));
}

export function getStrategy(id: string | null | undefined): InvestigationStrategy | null {
  if (!id) return null;
  return STRATEGIES.find((s) => s.id === id) ?? null;
}

/**
 * Select investigation strategy from title/description/template. Deterministic.
 */
export function selectStrategy(input: {
  title: string;
  description?: string | null;
  templateId?: string | null;
  strategyId?: string | null;
}): InvestigationStrategy {
  if (input.strategyId) {
    const forced = getStrategy(input.strategyId);
    if (forced) return forced;
  }

  const template = getTemplate(input.templateId);
  if (template) {
    const byTemplate = STRATEGIES.find((s) => s.templateId === template.id);
    if (byTemplate) return byTemplate;
    // Map remaining templates
    if (template.id === "government_audit") return getStrategy("compliance_investigation")!;
  }

  // KC-005 — explicit Government template IDs map into existing strategies.
  if (isGovernmentTemplateId(input.templateId)) {
    const govTpl = getGovernmentTemplate(input.templateId);
    const govStrategy = getStrategy(govTpl?.strategyId);
    if (govStrategy) return govStrategy;
  }

  // KC-006 — Labor template IDs map into existing strategies.
  if (isLaborTemplateId(input.templateId)) {
    const laborTpl = getLaborTemplate(input.templateId);
    const laborStrategy = getStrategy(laborTpl?.strategyId);
    if (laborStrategy) return laborStrategy;
  }

  const prompt = `${input.title}\n${input.description ?? ""}`;
  for (const hint of HINTS) {
    if (hint.re.test(prompt)) {
      return getStrategy(hint.strategyId)!;
    }
  }
  return getStrategy("general_investigation")!;
}
