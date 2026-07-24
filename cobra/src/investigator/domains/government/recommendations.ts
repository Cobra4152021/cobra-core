/** Government recommendation categories (KC-005). */

export type GovernmentRecommendationCategory =
  | "staffing"
  | "budgeting"
  | "policy"
  | "internal_control"
  | "documentation"
  | "technology"
  | "procurement"
  | "training"
  | "deployment"
  | "scheduling"
  | "reporting"
  | "management_review"
  | "further_investigation"
  | "legal_or_labor_review";

export interface GovernmentRecommendation {
  category: GovernmentRecommendationCategory;
  action: string;
  rationale: string;
  evidenceBasis: string[];
  expectedImpact: string;
  implementationDifficulty: "low" | "medium" | "high" | "unknown";
  estimatedResourceNeed: string | null;
  riskIfNotImplemented: string;
  dependencies: string[];
  ownerRole: string;
  proposedTimeframe: string;
  confidence: "high" | "medium" | "low" | "insufficient";
  furtherEvidenceRequired: boolean;
}

export const GOVERNMENT_RECOMMENDATION_CATEGORIES: GovernmentRecommendationCategory[] = [
  "staffing",
  "budgeting",
  "policy",
  "internal_control",
  "documentation",
  "technology",
  "procurement",
  "training",
  "deployment",
  "scheduling",
  "reporting",
  "management_review",
  "further_investigation",
  "legal_or_labor_review",
];

export function buildGovernmentRecommendation(
  input: Partial<GovernmentRecommendation> &
    Pick<GovernmentRecommendation, "category" | "action" | "rationale">,
): GovernmentRecommendation {
  return {
    category: input.category,
    action: input.action,
    rationale: input.rationale,
    evidenceBasis: input.evidenceBasis ?? [],
    expectedImpact: input.expectedImpact ?? "Impact depends on implementation and local context.",
    implementationDifficulty: input.implementationDifficulty ?? "unknown",
    estimatedResourceNeed: input.estimatedResourceNeed ?? null,
    riskIfNotImplemented:
      input.riskIfNotImplemented ?? "Unresolved issues may persist; monitor with additional evidence.",
    dependencies: input.dependencies ?? [],
    ownerRole: input.ownerRole ?? "management_review",
    proposedTimeframe: input.proposedTimeframe ?? "To be set by responsible unit",
    confidence: input.confidence ?? "medium",
    furtherEvidenceRequired: input.furtherEvidenceRequired ?? true,
  };
}
