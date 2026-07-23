/** Government investigation templates (KC-005) — 15 templates, deterministic. */

import type { GovernmentEvidenceCategoryId } from "./taxonomy.js";

export type GovernmentTemplateId =
  | "gov_overtime_analysis"
  | "gov_staffing_vacancy"
  | "gov_budget_variance"
  | "gov_department_budget_audit"
  | "gov_policy_compliance"
  | "gov_grant_compliance"
  | "gov_equipment_lifecycle"
  | "gov_fleet_cost"
  | "gov_training_compliance"
  | "gov_workload_deployment"
  | "gov_contract_mou_impact"
  | "gov_program_effectiveness"
  | "gov_procurement_review"
  | "gov_organizational_risk"
  | "gov_public_records_evidence";

export type GovernmentRiskLevel = "low" | "medium" | "high" | "critical";

export interface GovernmentTemplate {
  id: GovernmentTemplateId;
  version: string;
  title: string;
  objective: string;
  intendedUsers: string[];
  scopePrompts: string[];
  defaultQuestions: string[];
  defaultHypotheses: string[];
  requiredEvidenceCategories: GovernmentEvidenceCategoryId[];
  optionalEvidenceCategories: GovernmentEvidenceCategoryId[];
  knownLimitations: string[];
  riskLevel: GovernmentRiskLevel;
  confidenceRequirements: string[];
  reviewChecklist: string[];
  reportStructure: string[];
  recommendationCategories: string[];
  exclusions: string[];
  /** Maps to Investigator Strategy Engine StrategyId */
  strategyId: string;
  /** Evidence needed strings for planner compatibility */
  evidenceNeeded: string[];
  deliverables: string[];
}

const COMMON_REVIEW = [
  "Citations resolve to authorized org evidence",
  "Competing hypotheses retained",
  "Missing evidence listed",
  "No unsupported legal conclusions",
  "Sensitivity labels reviewed before publish",
];

const COMMON_REPORT = [
  "cover",
  "executive_summary",
  "scope",
  "methodology",
  "evidence_reviewed",
  "data_limitations",
  "competing_hypotheses",
  "findings",
  "missing_evidence",
  "recommendations",
  "citations",
];

function base(
  partial: Omit<GovernmentTemplate, "version" | "reportStructure" | "reviewChecklist"> & {
    reportStructure?: string[];
    reviewChecklist?: string[];
  },
): GovernmentTemplate {
  return {
    version: "0.1.0",
    reportStructure: partial.reportStructure ?? COMMON_REPORT,
    reviewChecklist: partial.reviewChecklist ?? COMMON_REVIEW,
    ...partial,
  };
}

export const GOVERNMENT_TEMPLATES: GovernmentTemplate[] = [
  base({
    id: "gov_overtime_analysis",
    title: "Overtime Analysis",
    objective:
      "Determine why overtime hours and/or costs changed over a defined fiscal period, without assuming a single cause.",
    intendedUsers: [
      "budget analysts",
      "sheriffs / police command",
      "auditors",
      "labor-management review teams",
      "executive leadership",
    ],
    scopePrompts: [
      "Which fiscal years and departments are in scope?",
      "Is the question about hours, cost, or both?",
      "Which bargaining units or classifications apply?",
    ],
    defaultQuestions: [
      "How did overtime hours and costs change across the fiscal years in scope?",
      "What were authorized, filled, and vacant positions during the period?",
      "How did leave, workers’ compensation, and training backfill affect coverage?",
      "Did minimum staffing, mandatory posts, special events, or mutual aid drive overtime?",
      "Did wage-rate or payroll-coding changes increase cost without increasing hours?",
      "What one-time operations, emergencies, or budget transfers affected overtime?",
      "What records are missing that would change the analysis?",
    ],
    defaultHypotheses: [
      "A. Overtime rose primarily because vacancies increased.",
      "B. Overtime rose because authorized staffing was insufficient.",
      "C. Overtime rose because leave or injury usage increased.",
      "D. Overtime rose because service demand or mandatory deployment increased.",
      "E. Overtime rose because wage rates increased rather than hours worked.",
      "F. Overtime rose because payroll coding or accounting treatment changed.",
      "G. Overtime rose because of special events, emergencies, or one-time operations.",
      "H. Multiple factors jointly caused the increase.",
    ],
    requiredEvidenceCategories: [
      "adopted_budget",
      "overtime_report",
      "position_control",
      "vacancy_report",
      "payroll",
    ],
    optionalEvidenceCategories: [
      "leave_report",
      "workers_compensation_record",
      "deployment_schedule",
      "labor_agreement",
      "mou",
      "workload_report",
      "expenditure_report",
    ],
    knownLimitations: [
      "Causal attribution requires aligned time series across staffing, leave, and overtime.",
      "Individual medical leave details must not appear in published reports.",
      "System does not assume vacancies are the cause before evidence analysis.",
    ],
    riskLevel: "high",
    confidenceRequirements: [
      "High confidence requires overtime actuals plus staffing/vacancy series from authoritative sources.",
      "Hours-versus-rate decomposition requires both hours and cost fields.",
    ],
    recommendationCategories: ["staffing", "budgeting", "scheduling", "reporting", "further_investigation"],
    exclusions: [
      "Not a disciplinary determination.",
      "Not a final labor-law conclusion.",
      "Not a payroll system replacement.",
    ],
    strategyId: "staffing_analysis",
    evidenceNeeded: [
      "approved budget",
      "overtime budget and actuals",
      "authorized and filled positions",
      "vacancy duration",
      "leave and workers’ compensation aggregates",
      "minimum staffing / relief factor",
      "special events and mutual aid logs",
      "labor agreement overtime rules",
      "payroll coding change notes",
    ],
    deliverables: [
      "overtime driver findings",
      "hours-versus-rate decomposition",
      "competing hypotheses",
      "evidence request list",
      "citation-backed government report",
    ],
  }),
  base({
    id: "gov_staffing_vacancy",
    title: "Staffing and Vacancy Analysis",
    objective: "Assess authorized, filled, active, and deployable staffing versus vacancies and service demand.",
    intendedUsers: ["HR analysts", "operations command", "budget office", "auditors"],
    scopePrompts: ["Which units and classifications?", "What as-of dates?", "Include academy pipeline?"],
    defaultQuestions: [
      "What were authorized, budgeted, filled, active, and deployable staffing levels?",
      "What is the vacancy rate and vacancy duration pattern?",
      "How do attrition, hiring lag, and academy yield affect the gap?",
      "How do overtime and leave relate to vacancies?",
    ],
    defaultHypotheses: [
      "Vacancies are the primary driver of capacity shortfall.",
      "Authorized staffing is below service demand even when fully filled.",
      "Leave and restricted duty reduce deployable staffing more than vacancies alone.",
      "Hiring pipeline delays prolong vacancies.",
      "Multiple factors jointly explain the staffing gap.",
    ],
    requiredEvidenceCategories: ["position_control", "vacancy_report", "staffing_roster"],
    optionalEvidenceCategories: [
      "leave_report",
      "overtime_report",
      "deployment_schedule",
      "organizational_chart",
      "training_record",
    ],
    knownLimitations: ["Do not infer missing headcount without labeling assumptions."],
    riskLevel: "high",
    confidenceRequirements: ["Vacancy rate requires authorized and filled counts for the same as-of date."],
    recommendationCategories: ["staffing", "training", "scheduling", "management_review"],
    exclusions: ["Not a hiring decision authority."],
    strategyId: "staffing_analysis",
    evidenceNeeded: ["position control", "vacancy reports", "rosters", "leave aggregates", "overtime"],
    deliverables: ["staffing metrics", "gap findings", "recommendations"],
  }),
  base({
    id: "gov_budget_variance",
    title: "Budget Variance Review",
    objective: "Compare adopted/revised budgets to actuals and identify documented, likely, and unresolved variances.",
    intendedUsers: ["budget analysts", "auditors", "department directors"],
    scopePrompts: ["Fiscal years?", "Funds and departments?", "Include encumbrances?"],
    defaultQuestions: [
      "What is adopted-to-actual and revised-to-actual variance?",
      "Which categories or programs drove movement?",
      "Were transfers and supplements authorized?",
      "Which costs are one-time versus recurring?",
    ],
    defaultHypotheses: [
      "Variance is explained by documented transfers or supplements.",
      "Variance is driven by overtime or salary savings.",
      "Variance reflects accounting classification changes.",
      "Material variance remains unresolved pending records.",
    ],
    requiredEvidenceCategories: ["adopted_budget", "revised_budget", "expenditure_report"],
    optionalEvidenceCategories: ["staff_report", "resolution", "grant_agreement", "contract"],
    knownLimitations: ["Not an audit opinion."],
    riskLevel: "medium",
    confidenceRequirements: ["Documented variance requires matching budget and expenditure sources."],
    recommendationCategories: ["budgeting", "internal_control", "reporting", "further_investigation"],
    exclusions: ["Not a legal determination of fund misuse."],
    strategyId: "budget_audit",
    evidenceNeeded: ["adopted budget", "revised budget", "actuals", "transfers", "encumbrances"],
    deliverables: ["variance findings", "unresolved items", "recommendations"],
  }),
  base({
    id: "gov_department_budget_audit",
    title: "Department Budget Audit",
    objective: "Review a department’s budget structure, controls, and multi-year spending patterns.",
    intendedUsers: ["auditors", "inspectors general", "finance"],
    scopePrompts: ["Department?", "Years?", "Funds?"],
    defaultQuestions: [
      "How did department spending change year over year?",
      "Are controls over transfers and overtime adequate based on evidence?",
      "What restricted or grant funds affect the picture?",
    ],
    defaultHypotheses: [
      "Spending growth aligns with authorized service expansion.",
      "Control weaknesses contribute to unexplained movement.",
      "Data quality issues limit conclusions.",
    ],
    requiredEvidenceCategories: ["adopted_budget", "expenditure_report", "organizational_chart"],
    optionalEvidenceCategories: ["audit_report", "grant_agreement", "procurement_record"],
    knownLimitations: ["Not a formal audit opinion unless issued by authorized auditor."],
    riskLevel: "high",
    confidenceRequirements: ["Control findings require policy/procedure plus transactional evidence."],
    recommendationCategories: ["budgeting", "internal_control", "documentation", "management_review"],
    exclusions: ["Not a criminal investigation."],
    strategyId: "budget_audit",
    evidenceNeeded: ["budgets", "actuals", "org chart", "prior audits"],
    deliverables: ["department findings", "control observations", "recommendations"],
  }),
  base({
    id: "gov_policy_compliance",
    title: "Policy Compliance Review",
    objective: "Compare required policy conditions to available implementation evidence without determining legal compliance.",
    intendedUsers: ["policy owners", "compliance officers", "auditors"],
    scopePrompts: ["Which policies?", "Period?", "Units covered?"],
    defaultQuestions: [
      "What does the current policy require, and which version was effective when?",
      "What training, acknowledgments, and approvals exist?",
      "Where does evidence suggest possible inconsistency or insufficiency?",
    ],
    defaultHypotheses: [
      "Evidence supports compliance with stated policy requirements.",
      "Evidence suggests possible inconsistency with policy.",
      "Insufficient evidence to assess key requirements.",
      "Policy version conflicts affect interpretation.",
    ],
    requiredEvidenceCategories: ["policy", "procedure"],
    optionalEvidenceCategories: ["training_record", "audit_report", "correspondence", "meeting_minutes"],
    knownLimitations: [
      "Do not independently determine legal compliance.",
      "Counsel or policy authority review may be required.",
    ],
    riskLevel: "medium",
    confidenceRequirements: ["Compliance support claims need mapped requirement-to-evidence links."],
    recommendationCategories: ["policy", "training", "documentation", "legal_or_labor_review"],
    exclusions: ["Not legal advice.", "Not a disciplinary finding."],
    strategyId: "policy_review",
    evidenceNeeded: ["policy versions", "procedures", "training records", "exceptions/waivers"],
    deliverables: ["compliance matrix labels", "gaps", "recommendations"],
  }),
  base({
    id: "gov_grant_compliance",
    title: "Grant Compliance Review",
    objective: "Review award terms against expenditures, reporting, and match requirements without final legal determination.",
    intendedUsers: ["grants managers", "auditors", "finance"],
    scopePrompts: ["Award number?", "Period?", "Programs?"],
    defaultQuestions: [
      "Were expenditures within the grant period and approved purpose?",
      "Are reports and deliverables complete?",
      "Is match documentation sufficient?",
    ],
    defaultHypotheses: [
      "Expenditures align with award terms.",
      "Missing reports or deliverables create compliance risk.",
      "Budget-category variance needs explanation.",
      "Match shortfall or unsupported expenditures exist.",
    ],
    requiredEvidenceCategories: ["grant_agreement", "expenditure_report"],
    optionalEvidenceCategories: ["procurement_record", "invoice", "staff_report", "correspondence"],
    knownLimitations: ["Not a final compliance determination."],
    riskLevel: "high",
    confidenceRequirements: ["Unsupported expenditure claims need invoice/PO linkage."],
    recommendationCategories: ["documentation", "internal_control", "reporting", "further_investigation"],
    exclusions: ["Not legal advice to the grantor or grantee."],
    strategyId: "compliance_investigation",
    evidenceNeeded: ["award", "budget", "expenditures", "reports", "match docs"],
    deliverables: ["grant risk findings", "missing items", "recommendations"],
  }),
  base({
    id: "gov_equipment_lifecycle",
    title: "Equipment Lifecycle Review",
    objective: "Assess equipment age, maintenance cost, downtime, and replacement priority from available records.",
    intendedUsers: ["asset managers", "public works", "budget"],
    scopePrompts: ["Asset classes?", "Period?", "Sites?"],
    defaultQuestions: [
      "What is lifecycle age versus expected useful life?",
      "Where is maintenance cost concentrated?",
      "Which assets show deferred-maintenance or safety risk signals?",
    ],
    defaultHypotheses: [
      "Replacement urgency is driven by age and downtime.",
      "Recurring repairs concentrate cost in a subset of assets.",
      "Inventory records are incomplete.",
    ],
    requiredEvidenceCategories: ["equipment_inventory"],
    optionalEvidenceCategories: ["fleet_record", "invoice", "purchase_order", "procurement_record"],
    knownLimitations: ["Safety recommendations require qualified technical review."],
    riskLevel: "medium",
    confidenceRequirements: ["Lifecycle age needs purchase date and expected life fields."],
    recommendationCategories: ["procurement", "budgeting", "technology", "management_review"],
    exclusions: ["Not an engineering certification."],
    strategyId: "technical_root_cause",
    evidenceNeeded: ["inventory", "purchase dates", "maintenance costs", "downtime"],
    deliverables: ["lifecycle risk findings", "replacement priority", "recommendations"],
  }),
  base({
    id: "gov_fleet_cost",
    title: "Fleet Cost Analysis",
    objective: "Analyze fleet acquisition, maintenance, usage, and cost concentration.",
    intendedUsers: ["fleet managers", "budget", "auditors"],
    scopePrompts: ["Fleet segments?", "Years?"],
    defaultQuestions: [
      "How do maintenance and fuel/usage costs trend?",
      "Which units drive cost concentration?",
      "Are replacement requests supported by usage and repair history?",
    ],
    defaultHypotheses: [
      "Cost growth tracks utilization.",
      "A small set of units drives disproportionate cost.",
      "Missing mileage/hours limits conclusions.",
    ],
    requiredEvidenceCategories: ["fleet_record", "expenditure_report"],
    optionalEvidenceCategories: ["equipment_inventory", "invoice", "procurement_record"],
    knownLimitations: ["Do not recommend public-safety vehicle cuts from incomplete data alone."],
    riskLevel: "medium",
    confidenceRequirements: ["Cost concentration requires unit-level cost fields."],
    recommendationCategories: ["procurement", "budgeting", "deployment", "further_investigation"],
    exclusions: ["Not a disposal authorization."],
    strategyId: "budget_audit",
    evidenceNeeded: ["fleet records", "maintenance costs", "usage hours/miles", "acquisition costs"],
    deliverables: ["cost findings", "replacement support assessment", "recommendations"],
  }),
  base({
    id: "gov_training_compliance",
    title: "Training Compliance Review",
    objective: "Assess required training completion and expiration risk using available records.",
    intendedUsers: ["training coordinators", "HR", "compliance"],
    scopePrompts: ["Required courses?", "Units?", "As-of date?"],
    defaultQuestions: [
      "What completion and expiration rates apply?",
      "Where are records missing or disputed?",
      "Which waivers or exceptions are pending?",
    ],
    defaultHypotheses: [
      "Most required training is current.",
      "Expiration risk is concentrated in specific courses or units.",
      "Missing records prevent confirmation.",
    ],
    requiredEvidenceCategories: ["training_record", "policy"],
    optionalEvidenceCategories: ["procedure", "correspondence"],
    knownLimitations: ["Do not expose unnecessary individual personnel information."],
    riskLevel: "medium",
    confidenceRequirements: ["Completion rate needs required roster and completion evidence."],
    recommendationCategories: ["training", "documentation", "policy", "management_review"],
    exclusions: ["Not a licensing board determination."],
    strategyId: "compliance_investigation",
    evidenceNeeded: ["required courses", "completion records", "expiration dates", "waivers"],
    deliverables: ["compliance status labels", "gaps", "recommendations"],
  }),
  base({
    id: "gov_workload_deployment",
    title: "Workload and Deployment Analysis",
    objective: "Relate service demand, staffing, and overtime where records support calculation.",
    intendedUsers: ["operations command", "analysts", "auditors"],
    scopePrompts: ["Geography?", "Shifts?", "Period?"],
    defaultQuestions: [
      "How did calls/workload units change versus staffing?",
      "Where do peak-demand periods create mismatch?",
      "How does overtime relate to workload units?",
    ],
    defaultHypotheses: [
      "Demand growth outpaced deployable staffing.",
      "Deployment policy, not demand, drives overtime.",
      "Data definitions changed, limiting trend comparison.",
    ],
    requiredEvidenceCategories: ["workload_report", "deployment_schedule"],
    optionalEvidenceCategories: ["overtime_report", "incident_summary", "leave_report", "vacancy_report"],
    knownLimitations: ["Do not make public-safety recommendations solely from incomplete numerical data."],
    riskLevel: "high",
    confidenceRequirements: ["Staffing-to-demand ratio needs aligned definitions and periods."],
    recommendationCategories: ["deployment", "scheduling", "staffing", "further_investigation"],
    exclusions: ["Not an operational command decision."],
    strategyId: "staffing_analysis",
    evidenceNeeded: ["CFS/workload", "shift staffing", "overtime", "leave", "deployment policies"],
    deliverables: ["workload metrics", "mismatch findings", "recommendations"],
  }),
  base({
    id: "gov_contract_mou_impact",
    title: "Contract or MOU Operational Impact Review",
    objective: "Assess how contract/MOU terms affect staffing, overtime, or budget operations.",
    intendedUsers: ["labor relations", "operations", "budget", "legal liaison"],
    scopePrompts: ["Agreements in scope?", "Period?"],
    defaultQuestions: [
      "Which contractual minimums or premiums affect overtime?",
      "Is practice consistent with agreement text in evidence?",
      "What operational impacts are documented?",
    ],
    defaultHypotheses: [
      "Agreement terms are a material overtime driver.",
      "Practice diverges from written terms.",
      "Insufficient agreement text to assess impact.",
    ],
    requiredEvidenceCategories: ["labor_agreement"],
    optionalEvidenceCategories: ["mou", "overtime_report", "payroll", "policy"],
    knownLimitations: ["Not a grievance decision or bargaining mandate."],
    riskLevel: "high",
    confidenceRequirements: ["Impact claims need agreement text plus operational metrics."],
    recommendationCategories: ["legal_or_labor_review", "staffing", "budgeting", "documentation"],
    exclusions: ["Not legal advice."],
    strategyId: "union_contract_review",
    evidenceNeeded: ["MOU/CBA", "overtime rules", "staffing minimums", "payroll extracts"],
    deliverables: ["impact findings", "practice gaps", "recommendations"],
  }),
  base({
    id: "gov_program_effectiveness",
    title: "Program Effectiveness Review",
    objective: "Evaluate whether program outputs and costs align with stated objectives using available evidence.",
    intendedUsers: ["program managers", "auditors", "executive leadership"],
    scopePrompts: ["Program?", "Outcomes metrics?", "Period?"],
    defaultQuestions: [
      "What objectives and metrics were defined?",
      "What outputs/outcomes are evidenced?",
      "How do costs compare to results?",
    ],
    defaultHypotheses: [
      "Program met documented objectives.",
      "Objectives lack measurable criteria.",
      "Cost growth is not matched by outcome evidence.",
    ],
    requiredEvidenceCategories: ["staff_report", "expenditure_report"],
    optionalEvidenceCategories: ["grant_agreement", "workload_report", "public_data", "audit_report"],
    knownLimitations: ["Effectiveness is not a political endorsement or rejection."],
    riskLevel: "medium",
    confidenceRequirements: ["Outcome claims need defined metrics and source data."],
    recommendationCategories: ["management_review", "reporting", "budgeting", "further_investigation"],
    exclusions: ["Not a funding appropriation."],
    strategyId: "research_investigation",
    evidenceNeeded: ["program goals", "performance metrics", "expenditures", "evaluations"],
    deliverables: ["effectiveness findings", "data gaps", "recommendations"],
  }),
  base({
    id: "gov_procurement_review",
    title: "Procurement Review",
    objective: "Review procurement documentation for completeness, competition indicators, and control gaps.",
    intendedUsers: ["purchasing", "auditors", "finance"],
    scopePrompts: ["Solicitations?", "Dollar threshold?", "Period?"],
    defaultQuestions: [
      "Is the competition/file complete?",
      "Do invoices and POs align with awards?",
      "Where are approvals missing?",
    ],
    defaultHypotheses: [
      "Procurement file supports the award path.",
      "Documentation gaps create control weakness.",
      "Change orders lack authorization evidence.",
    ],
    requiredEvidenceCategories: ["procurement_record", "contract"],
    optionalEvidenceCategories: ["purchase_order", "invoice", "resolution"],
    knownLimitations: ["Not a determination of procurement law violation."],
    riskLevel: "medium",
    confidenceRequirements: ["Control weakness claims need missing-document criteria."],
    recommendationCategories: ["procurement", "internal_control", "documentation"],
    exclusions: ["Not a vendor debarment action."],
    strategyId: "compliance_investigation",
    evidenceNeeded: ["solicitation file", "award", "contract", "POs", "invoices"],
    deliverables: ["procurement findings", "gaps", "recommendations"],
  }),
  base({
    id: "gov_organizational_risk",
    title: "Organizational Risk Assessment",
    objective: "Identify operational, fiscal, and control risks from available evidence without sensational claims.",
    intendedUsers: ["executive leadership", "risk managers", "auditors"],
    scopePrompts: ["Enterprise or unit?", "Risk domains?"],
    defaultQuestions: [
      "What material risks are evidenced?",
      "Which controls appear present or weak?",
      "What unresolved issues require further investigation?",
    ],
    defaultHypotheses: [
      "Primary risks are fiscal/staffing capacity.",
      "Primary risks are control/documentation gaps.",
      "Evidence is insufficient for enterprise conclusions.",
    ],
    requiredEvidenceCategories: ["audit_report", "organizational_chart"],
    optionalEvidenceCategories: [
      "adopted_budget",
      "policy",
      "vacancy_report",
      "workload_report",
    ],
    knownLimitations: ["Risk assessment is not a prediction of failure or misconduct."],
    riskLevel: "high",
    confidenceRequirements: ["Material risk statements need cited evidence and limitations."],
    recommendationCategories: ["management_review", "internal_control", "further_investigation"],
    exclusions: ["Not an insurance actuarial opinion."],
    strategyId: "general_investigation",
    evidenceNeeded: ["prior audits", "org structure", "key metrics", "policies"],
    deliverables: ["risk findings", "control observations", "recommendations"],
  }),
  base({
    id: "gov_public_records_evidence",
    title: "Public Records Evidence Review",
    objective: "Inventory and evaluate publicly available or released records for an investigation question.",
    intendedUsers: ["analysts", "clerks", "investigators"],
    scopePrompts: ["Records sets?", "Date range?", "Agencies?"],
    defaultQuestions: [
      "What public records are available and authoritative?",
      "Where do sources conflict?",
      "What remains unavailable or redacted?",
    ],
    defaultHypotheses: [
      "Public records suffice for preliminary findings.",
      "Key records are missing or redacted.",
      "Source conflicts require internal corroboration.",
    ],
    requiredEvidenceCategories: ["public_data"],
    optionalEvidenceCategories: [
      "agenda_item",
      "meeting_minutes",
      "ordinance",
      "resolution",
      "staff_report",
    ],
    knownLimitations: ["Public records may omit privileged or personnel content."],
    riskLevel: "low",
    confidenceRequirements: ["Cite dataset version/URL or release packet."],
    recommendationCategories: ["documentation", "further_investigation", "reporting"],
    exclusions: ["Not a public-records legal advice service."],
    strategyId: "evidence_review",
    evidenceNeeded: ["public datasets", "agendas/minutes", "ordinances", "staff reports"],
    deliverables: ["evidence inventory", "conflicts", "gaps", "recommendations"],
  }),
];

export function listGovernmentTemplates(): GovernmentTemplate[] {
  return GOVERNMENT_TEMPLATES.map((t) => ({ ...t }));
}

export function getGovernmentTemplate(id: string | null | undefined): GovernmentTemplate | null {
  if (!id) return null;
  return GOVERNMENT_TEMPLATES.find((t) => t.id === id) ?? null;
}

export function isGovernmentTemplateId(id: string | null | undefined): id is GovernmentTemplateId {
  return Boolean(id && GOVERNMENT_TEMPLATES.some((t) => t.id === id));
}
