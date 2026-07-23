/** Cobra Investigator domain types (KC-004). Storage-independent. */

export type InvestigationStatus =
  | "draft"
  | "planning"
  | "collecting_evidence"
  | "analyzing"
  | "review"
  | "completed"
  | "archived";

export type ConfidenceLevel = "high" | "medium" | "low" | "insufficient_evidence";

export type Priority = "critical" | "high" | "medium" | "low";

export interface InvestigationPlan {
  goal: string;
  questions: string[];
  evidenceNeeded: string[];
  knownFacts: string[];
  unknownFacts: string[];
  assumptions: string[];
  steps: string[];
  priority: Priority;
  deliverables: string[];
  templateId: string | null;
}

export interface FindingDraft {
  title: string;
  summary: string;
  confidence: ConfidenceLevel;
  citations: string[];
  evidence: string[];
  entityIds: string[];
  timelineRefs: string[];
}

export interface RecommendationDraft {
  title: string;
  body: string;
  priority: Priority;
  reason: string;
  findingIndexes: number[];
  evidence: string[];
  expectedImpact: string;
  confidence: ConfidenceLevel;
}

export interface ReportSections {
  executiveSummary: string;
  scope: string;
  questions: string[];
  evidenceReviewed: string[];
  timeline: string[];
  findings: string[];
  conflicts: string[];
  recommendations: string[];
  appendix: string[];
  citations: string[];
}
