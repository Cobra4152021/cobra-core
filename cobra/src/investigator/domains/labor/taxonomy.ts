/** Labor evidence taxonomy (KC-006). */

export type LaborEvidenceCategoryId =
  | "collective_bargaining_agreement"
  | "mou"
  | "side_letter"
  | "arbitration_award"
  | "settlement"
  | "grievance"
  | "email"
  | "payroll"
  | "schedule"
  | "staffing_report"
  | "policy"
  | "directive"
  | "personnel_order"
  | "meeting_minutes"
  | "past_practice"
  | "training_bulletin"
  | "personnel_notice"
  | "letter_of_agreement"
  | "other";

export interface LaborEvidenceCategory {
  id: LaborEvidenceCategoryId;
  label: string;
  privacySensitivity: "public" | "internal" | "labor_relations" | "personnel" | "unknown";
  notes: string;
}

export const LABOR_EVIDENCE_CATEGORIES: LaborEvidenceCategory[] = [
  { id: "collective_bargaining_agreement", label: "Collective Bargaining Agreement", privacySensitivity: "labor_relations", notes: "Version and effective dates required." },
  { id: "mou", label: "MOU", privacySensitivity: "labor_relations", notes: "May amend CBA; track supersession." },
  { id: "side_letter", label: "Side Letter", privacySensitivity: "labor_relations", notes: "Often omitted from bound volumes." },
  { id: "arbitration_award", label: "Arbitration Award", privacySensitivity: "labor_relations", notes: "Not a precedent unless parties treat as such." },
  { id: "settlement", label: "Settlement", privacySensitivity: "labor_relations", notes: "May be confidential." },
  { id: "grievance", label: "Grievance", privacySensitivity: "personnel", notes: "Restrict individual identifiers in published reports." },
  { id: "email", label: "Email", privacySensitivity: "internal", notes: "Incomplete threads common." },
  { id: "payroll", label: "Payroll", privacySensitivity: "personnel", notes: "Aggregate preferred for reports." },
  { id: "schedule", label: "Schedule", privacySensitivity: "internal", notes: "May be security-sensitive for public safety." },
  { id: "staffing_report", label: "Staffing Report", privacySensitivity: "internal", notes: "Reuse Government staffing metrics where applicable." },
  { id: "policy", label: "Policy", privacySensitivity: "public", notes: "Track effective version." },
  { id: "directive", label: "Directive", privacySensitivity: "internal", notes: "May conflict with CBA." },
  { id: "personnel_order", label: "Personnel Order", privacySensitivity: "personnel", notes: "Restrict PII." },
  { id: "meeting_minutes", label: "Meeting Minutes", privacySensitivity: "internal", notes: "Draft vs approved." },
  { id: "past_practice", label: "Past Practice", privacySensitivity: "labor_relations", notes: "Requires duration/consistency evidence." },
  { id: "training_bulletin", label: "Training Bulletin", privacySensitivity: "internal", notes: "May evidence notice." },
  { id: "personnel_notice", label: "Personnel Notice", privacySensitivity: "personnel", notes: "Restrict PII." },
  { id: "letter_of_agreement", label: "Letter of Agreement", privacySensitivity: "labor_relations", notes: "Track expiration." },
  { id: "other", label: "Other", privacySensitivity: "unknown", notes: "Classify before publish." },
];

export function getLaborEvidenceCategory(id: string): LaborEvidenceCategory | null {
  return LABOR_EVIDENCE_CATEGORIES.find((c) => c.id === id) ?? null;
}
