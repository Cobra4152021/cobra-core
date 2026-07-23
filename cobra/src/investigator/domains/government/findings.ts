/** Government finding classifications (KC-005). */

export type GovernmentFindingClass =
  | "budget_variance"
  | "staffing_gap"
  | "overtime_driver"
  | "policy_inconsistency"
  | "missing_documentation"
  | "control_weakness"
  | "process_delay"
  | "operational_risk"
  | "compliance_concern"
  | "data_quality_issue"
  | "cost_concentration"
  | "lifecycle_risk"
  | "training_gap"
  | "workload_mismatch"
  | "unresolved_issue"
  | "positive_control"
  | "effective_practice";

export type StatementKind =
  | "fact"
  | "inference"
  | "allegation"
  | "hypothesis"
  | "professional_judgment"
  | "unresolved_issue";

export interface GovernmentFinding {
  classification: GovernmentFindingClass;
  issue: string;
  criteria: string;
  condition: string;
  cause: string | null;
  effectOrRisk: string;
  supportingEvidence: string[];
  contraryEvidence: string[];
  confidence: "high" | "medium" | "low" | "insufficient";
  materiality: "high" | "medium" | "low" | "unknown";
  responsibleUnit: string | null;
  limitations: string[];
  recommendedReview: string;
  statementKind: StatementKind;
}

export const GOVERNMENT_FINDING_CLASSES: GovernmentFindingClass[] = [
  "budget_variance",
  "staffing_gap",
  "overtime_driver",
  "policy_inconsistency",
  "missing_documentation",
  "control_weakness",
  "process_delay",
  "operational_risk",
  "compliance_concern",
  "data_quality_issue",
  "cost_concentration",
  "lifecycle_risk",
  "training_gap",
  "workload_mismatch",
  "unresolved_issue",
  "positive_control",
  "effective_practice",
];

export function buildGovernmentFinding(
  input: Partial<GovernmentFinding> &
    Pick<GovernmentFinding, "classification" | "issue" | "criteria" | "condition">,
): GovernmentFinding {
  return {
    classification: input.classification,
    issue: input.issue,
    criteria: input.criteria,
    condition: input.condition,
    cause: input.cause ?? null,
    effectOrRisk: input.effectOrRisk ?? "Effect/risk not yet established from available evidence.",
    supportingEvidence: input.supportingEvidence ?? [],
    contraryEvidence: input.contraryEvidence ?? [],
    confidence: input.confidence ?? "insufficient",
    materiality: input.materiality ?? "unknown",
    responsibleUnit: input.responsibleUnit ?? null,
    limitations: input.limitations ?? ["Based only on records provided to Cobra Government."],
    recommendedReview: input.recommendedReview ?? "Human review required before action.",
    statementKind: input.statementKind ?? "unresolved_issue",
  };
}

/** Soft guard: refuse high-confidence misconduct language without support. */
export function sanitizeGovernmentFindingLanguage(text: string): {
  text: string;
  blockedClaim: boolean;
} {
  const blocked =
    /\b(fraud|corruption|criminal|guilty|misconduct|discrimination)\b/i.test(text) &&
    !/\b(alleged|allegation|hypothesis|insufficient evidence|not established)\b/i.test(text);
  if (!blocked) return { text, blockedClaim: false };
  return {
    text: `${text.trim()} [Relabeled: unsupported misconduct/legal conclusion — requires authorized review and sufficient evidence.]`,
    blockedClaim: true,
  };
}
