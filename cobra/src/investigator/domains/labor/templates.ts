/** Labor investigation templates (KC-006) — 14 templates, deterministic. */

import type { LaborEvidenceCategoryId } from "./taxonomy.js";

export type LaborTemplateId =
  | "labor_contract_compliance"
  | "labor_grievance_preparation"
  | "labor_arbitration_preparation"
  | "labor_mandatory_overtime"
  | "labor_staffing_compliance"
  | "labor_relief_factor"
  | "labor_promotion_review"
  | "labor_discipline_review"
  | "labor_past_practice"
  | "labor_leave_administration"
  | "labor_schedule_compliance"
  | "labor_negotiation_preparation"
  | "labor_contract_comparison"
  | "labor_management_issue_review";

export interface LaborTemplate {
  id: LaborTemplateId;
  version: string;
  title: string;
  objective: string;
  intendedUsers: string[];
  defaultQuestions: string[];
  defaultHypotheses: string[];
  requiredEvidenceCategories: LaborEvidenceCategoryId[];
  optionalEvidenceCategories: LaborEvidenceCategoryId[];
  knownLimitations: string[];
  riskLevel: "low" | "medium" | "high" | "critical";
  strategyId: string;
  evidenceNeeded: string[];
  deliverables: string[];
  exclusions: string[];
}

function t(
  partial: Omit<LaborTemplate, "version"> & { version?: string },
): LaborTemplate {
  return { version: "0.1.0", ...partial };
}

export const LABOR_TEMPLATES: LaborTemplate[] = [
  t({
    id: "labor_contract_compliance",
    title: "Contract Compliance",
    objective: "Compare practice and records to cited CBA/MOU articles without determining breach.",
    intendedUsers: ["labor relations", "union reps", "management", "auditors"],
    defaultQuestions: [
      "Which articles govern the issue?",
      "What practice or records are alleged to conflict with those articles?",
      "What competing readings of the language exist?",
      "What evidence is missing?",
    ],
    defaultHypotheses: [
      "Records are consistent with the cited articles.",
      "Records suggest possible inconsistency requiring human determination.",
      "Ambiguous language prevents a compliance conclusion.",
      "Past practice may inform interpretation if supported.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement"],
    optionalEvidenceCategories: ["mou", "side_letter", "policy", "schedule", "payroll"],
    knownLimitations: ["Not a breach determination.", "Not legal advice."],
    riskLevel: "high",
    strategyId: "union_contract_review",
    evidenceNeeded: ["CBA/MOU text", "practice records", "related policies"],
    deliverables: ["article map", "competing readings", "missing evidence", "labor report"],
    exclusions: ["Not an unfair labor practice finding."],
  }),
  t({
    id: "labor_grievance_preparation",
    title: "Grievance Preparation",
    objective: "Assemble issue, timeline, facts, articles, and evidence for human-reviewed grievance drafting.",
    intendedUsers: ["union stewards", "labor relations", "investigators"],
    defaultQuestions: [
      "What is the precise issue and when did it arise?",
      "Which articles and policies are cited?",
      "What supporting and contrary evidence exists?",
      "What witnesses and past practice claims are alleged?",
    ],
    defaultHypotheses: [
      "Available evidence supports proceeding to a draft grievance for review.",
      "Evidence is incomplete; draft should flag gaps.",
      "Competing explanations remain unresolved.",
    ],
    requiredEvidenceCategories: ["grievance", "collective_bargaining_agreement"],
    optionalEvidenceCategories: ["email", "schedule", "payroll", "past_practice", "policy"],
    knownLimitations: ["Drafts require human review before filing."],
    riskLevel: "high",
    strategyId: "union_contract_review",
    evidenceNeeded: ["issue statement", "timeline", "articles", "exhibits"],
    deliverables: ["draft grievance packet", "exhibit list", "missing evidence"],
    exclusions: ["Not a filing authorization."],
  }),
  t({
    id: "labor_arbitration_preparation",
    title: "Arbitration Preparation",
    objective: "Organize exhibits, witnesses, timeline, and questions for arbitration prep without predicting outcomes.",
    intendedUsers: ["advocates", "labor relations", "investigators"],
    defaultQuestions: [
      "What is the framed issue for arbitration?",
      "What exhibits and witnesses support each side?",
      "What contrary evidence must be addressed?",
      "What questions remain unresolved?",
    ],
    defaultHypotheses: [
      "Exhibit index is citation-backed and complete for known records.",
      "Key exhibits or witnesses are missing.",
      "Issue framing remains disputed.",
    ],
    requiredEvidenceCategories: ["grievance", "collective_bargaining_agreement"],
    optionalEvidenceCategories: ["arbitration_award", "settlement", "email", "payroll", "schedule"],
    knownLimitations: ["Does not predict arbitral outcomes."],
    riskLevel: "high",
    strategyId: "union_contract_review",
    evidenceNeeded: ["issue", "exhibits", "witnesses", "timeline"],
    deliverables: ["exhibit index", "witness list", "unresolved questions"],
    exclusions: ["Not legal advice to either party."],
  }),
  t({
    id: "labor_mandatory_overtime",
    title: "Mandatory Overtime Review",
    objective: "Analyze mandatory overtime against contract rules, staffing, and schedules using available evidence.",
    intendedUsers: ["operations", "labor relations", "budget analysts"],
    defaultQuestions: [
      "What overtime was mandatory versus voluntary?",
      "Which contract rules govern holdovers and mandates?",
      "How did vacancies and leave affect overtime?",
    ],
    defaultHypotheses: [
      "Mandatory overtime aligns with cited staffing/overtime articles.",
      "Vacancies or leave are the primary drivers.",
      "Scheduling practice diverges from written rules.",
      "Multiple factors jointly explain the overtime.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement", "payroll", "schedule"],
    optionalEvidenceCategories: ["staffing_report", "mou", "email"],
    knownLimitations: ["Reuses Government overtime/staffing metrics where fields exist."],
    riskLevel: "high",
    strategyId: "staffing_analysis",
    evidenceNeeded: ["OT logs", "schedules", "CBA OT articles", "vacancies"],
    deliverables: ["OT findings", "competing hypotheses", "labor report"],
    exclusions: ["Not a wage claim adjudication."],
  }),
  t({
    id: "labor_staffing_compliance",
    title: "Staffing Compliance",
    objective: "Compare staffing levels to contract minimums and assignment language without determining breach.",
    intendedUsers: ["operations", "labor relations", "HR"],
    defaultQuestions: [
      "What minimum staffing or assignment language applies?",
      "What were authorized, filled, and deployable levels?",
      "How were vacancies and holdovers handled?",
    ],
    defaultHypotheses: [
      "Staffing met cited contractual minimums in the period.",
      "Records suggest possible shortfalls requiring human review.",
      "Insufficient records to assess compliance.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement", "staffing_report"],
    optionalEvidenceCategories: ["schedule", "payroll", "mou"],
    knownLimitations: ["Reuses Government staffing metrics."],
    riskLevel: "high",
    strategyId: "staffing_analysis",
    evidenceNeeded: ["minimum staffing language", "rosters", "vacancy reports"],
    deliverables: ["staffing metrics", "article map", "gaps"],
    exclusions: ["Not a staffing mandate."],
  }),
  t({
    id: "labor_relief_factor",
    title: "Relief Factor Review",
    objective: "Assess relief factor assumptions against leave, training, and vacancy evidence.",
    intendedUsers: ["budget", "operations", "labor relations"],
    defaultQuestions: [
      "What relief factor was used or bargained?",
      "How do leave and training affect deployable staffing?",
      "Is the factor supported by contemporaneous data?",
    ],
    defaultHypotheses: [
      "Relief factor is supported by leave/vacancy evidence.",
      "Relief factor understates non-deployable time.",
      "Data insufficient to validate the factor.",
    ],
    requiredEvidenceCategories: ["staffing_report"],
    optionalEvidenceCategories: ["payroll", "schedule", "collective_bargaining_agreement"],
    knownLimitations: ["Assumptions must be labeled."],
    riskLevel: "medium",
    strategyId: "staffing_analysis",
    evidenceNeeded: ["relief factor definition", "leave aggregates", "vacancies"],
    deliverables: ["relief analysis", "assumptions", "recommendations"],
    exclusions: ["Not an actuarial certification."],
  }),
  t({
    id: "labor_promotion_review",
    title: "Promotion Review",
    objective: "Review promotion process evidence against CBA/policy criteria without determining discrimination or liability.",
    intendedUsers: ["HR", "labor relations", "investigators"],
    defaultQuestions: [
      "What promotion criteria and seniority rules apply?",
      "What process evidence exists?",
      "Where are records missing?",
    ],
    defaultHypotheses: [
      "Process evidence aligns with cited rules.",
      "Gaps in documentation prevent confirmation.",
      "Competing explanations of the selection remain.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement", "personnel_order"],
    optionalEvidenceCategories: ["policy", "email", "meeting_minutes"],
    knownLimitations: ["Not a discrimination determination."],
    riskLevel: "high",
    strategyId: "policy_review",
    evidenceNeeded: ["promotion article", "eligibility lists", "selection records"],
    deliverables: ["process timeline", "gaps", "labor report"],
    exclusions: ["Not a hiring authority decision."],
  }),
  t({
    id: "labor_discipline_review",
    title: "Discipline Review",
    objective: "Organize discipline-related facts, articles, and evidence for review without determining just cause.",
    intendedUsers: ["labor relations", "union reps", "investigators"],
    defaultQuestions: [
      "What disciplinary action and dates are at issue?",
      "Which progressive discipline or just-cause articles apply?",
      "What supporting and mitigating evidence exists?",
    ],
    defaultHypotheses: [
      "Record is complete for human just-cause review.",
      "Key notice or investigation records are missing.",
      "Past practice claims require additional evidence.",
    ],
    requiredEvidenceCategories: ["personnel_notice", "collective_bargaining_agreement"],
    optionalEvidenceCategories: ["email", "policy", "grievance", "past_practice"],
    knownLimitations: ["Not a just-cause determination."],
    riskLevel: "critical",
    strategyId: "union_contract_review",
    evidenceNeeded: ["discipline notice", "investigation file", "articles"],
    deliverables: ["timeline", "exhibit list", "gaps"],
    exclusions: ["Not a disciplinary finding."],
  }),
  t({
    id: "labor_past_practice",
    title: "Past Practice Investigation",
    objective: "Evaluate claims of past practice using duration, consistency, and exception evidence.",
    intendedUsers: ["labor relations", "advocates", "investigators"],
    defaultQuestions: [
      "What practice is alleged?",
      "How long and how consistently was it followed?",
      "What exceptions and written policy exist?",
    ],
    defaultHypotheses: [
      "Evidence supports a consistent long-standing practice.",
      "Exceptions undermine consistency.",
      "Written policy supersedes or conflicts with practice claims.",
      "Insufficient evidence to establish past practice.",
    ],
    requiredEvidenceCategories: ["past_practice"],
    optionalEvidenceCategories: ["schedule", "email", "policy", "collective_bargaining_agreement"],
    knownLimitations: ["Past practice doctrines vary; human determination required."],
    riskLevel: "high",
    strategyId: "evidence_review",
    evidenceNeeded: ["practice instances", "duration", "exceptions", "policy text"],
    deliverables: ["practice matrix", "confidence", "gaps"],
    exclusions: ["Not a binding past-practice ruling."],
  }),
  t({
    id: "labor_leave_administration",
    title: "Leave Administration",
    objective: "Review leave administration against CBA/policy using available records.",
    intendedUsers: ["HR", "labor relations"],
    defaultQuestions: [
      "Which leave articles and policies apply?",
      "Are approvals and denials documented?",
      "Where do records conflict?",
    ],
    defaultHypotheses: [
      "Administration aligns with cited leave rules.",
      "Documentation gaps exist.",
      "Competing interpretations of leave categories remain.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement", "payroll"],
    optionalEvidenceCategories: ["policy", "email", "personnel_notice"],
    knownLimitations: ["Do not expose medical details."],
    riskLevel: "medium",
    strategyId: "policy_review",
    evidenceNeeded: ["leave articles", "leave logs", "approvals"],
    deliverables: ["leave findings", "gaps", "recommendations"],
    exclusions: ["Not a medical determination."],
  }),
  t({
    id: "labor_schedule_compliance",
    title: "Schedule Compliance",
    objective: "Compare schedules and shift bids to contract scheduling rules.",
    intendedUsers: ["operations", "labor relations"],
    defaultQuestions: [
      "What scheduling and seniority/bid rules apply?",
      "Were schedules posted and changed per cited rules?",
      "How do holdovers interact with the schedule?",
    ],
    defaultHypotheses: [
      "Schedules align with cited rules.",
      "Change-notice or bid records are incomplete.",
      "Practice diverges from written scheduling articles.",
    ],
    requiredEvidenceCategories: ["schedule", "collective_bargaining_agreement"],
    optionalEvidenceCategories: ["email", "staffing_report", "mou"],
    knownLimitations: ["Limit operational detail in public reports."],
    riskLevel: "medium",
    strategyId: "staffing_analysis",
    evidenceNeeded: ["schedules", "bid sheets", "scheduling articles"],
    deliverables: ["schedule timeline", "gaps", "labor report"],
    exclusions: ["Not an operational command decision."],
  }),
  t({
    id: "labor_negotiation_preparation",
    title: "Negotiation Preparation",
    objective: "Track proposals and summarize open issues and article impacts for bargaining prep.",
    intendedUsers: ["negotiators", "labor relations", "executive leadership"],
    defaultQuestions: [
      "What are current union and management proposals?",
      "Which articles would change?",
      "What open issues remain?",
    ],
    defaultHypotheses: [
      "Proposal packages are complete for known issues.",
      "Cost/impact data are incomplete.",
      "Tentative agreements need documentation.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement"],
    optionalEvidenceCategories: ["mou", "meeting_minutes", "staffing_report", "payroll"],
    knownLimitations: ["Not a bargaining mandate or cost guarantee."],
    riskLevel: "high",
    strategyId: "union_contract_review",
    evidenceNeeded: ["proposals", "current CBA", "impact notes"],
    deliverables: ["change summary", "open issues", "impact summary"],
    exclusions: ["Not a tentative agreement execution."],
  }),
  t({
    id: "labor_contract_comparison",
    title: "Contract Comparison",
    objective: "Compare two agreement versions and surface language/benefit/staffing changes without legal conclusions.",
    intendedUsers: ["negotiators", "labor relations", "clerks"],
    defaultQuestions: [
      "Which versions are being compared?",
      "What articles were added, removed, or modified?",
      "Which changes affect overtime, leave, staffing, or discipline?",
    ],
    defaultHypotheses: [
      "Changes are limited to documented article diffs.",
      "Renumbering may obscure substantive changes.",
      "Side letters may be missing from one package.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement"],
    optionalEvidenceCategories: ["mou", "side_letter", "letter_of_agreement"],
    knownLimitations: ["Text diff is not a legal interpretation."],
    riskLevel: "medium",
    strategyId: "evidence_review",
    evidenceNeeded: ["old agreement", "new agreement", "effective dates"],
    deliverables: ["diff summary", "renumber map", "open questions"],
    exclusions: ["Not an adoption recommendation."],
  }),
  t({
    id: "labor_management_issue_review",
    title: "Labor-Management Issue Review",
    objective: "General labor-management issue investigation with competing explanations and evidence gaps.",
    intendedUsers: ["labor-management committees", "investigators"],
    defaultQuestions: [
      "What is the issue statement?",
      "What contract and practice evidence applies?",
      "What patterns appear across similar issues?",
    ],
    defaultHypotheses: [
      "Issue is primarily contractual language ambiguity.",
      "Issue is primarily operational/staffing capacity.",
      "Issue is primarily documentation/process gaps.",
      "Multiple factors jointly apply.",
    ],
    requiredEvidenceCategories: ["collective_bargaining_agreement"],
    optionalEvidenceCategories: ["email", "grievance", "meeting_minutes", "staffing_report"],
    knownLimitations: ["Do not infer wrongdoing from patterns alone."],
    riskLevel: "medium",
    strategyId: "general_investigation",
    evidenceNeeded: ["issue brief", "articles", "related grievances"],
    deliverables: ["findings", "patterns", "recommendations"],
    exclusions: ["Not a ULP charge."],
  }),
];

export function listLaborTemplates(): LaborTemplate[] {
  return LABOR_TEMPLATES.map((x) => ({ ...x }));
}

export function getLaborTemplate(id: string | null | undefined): LaborTemplate | null {
  if (!id) return null;
  return LABOR_TEMPLATES.find((x) => x.id === id) ?? null;
}

export function isLaborTemplateId(id: string | null | undefined): id is LaborTemplateId {
  return Boolean(id && LABOR_TEMPLATES.some((x) => x.id === id));
}
