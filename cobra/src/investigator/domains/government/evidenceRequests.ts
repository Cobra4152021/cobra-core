/** Internal evidence request tracking for Government investigations (KC-005). */

import type { GovernmentTemplate } from "./templates.js";
import type { GovernmentEvidenceCategoryId } from "./taxonomy.js";

export type EvidenceRequestStatus =
  | "needed"
  | "requested"
  | "partially_received"
  | "received"
  | "unavailable"
  | "declined"
  | "not_applicable";

export interface GovernmentEvidenceRequest {
  id: string;
  requestedRecord: string;
  category: GovernmentEvidenceCategoryId | "other";
  reasonNeeded: string;
  dateRange: string | null;
  departmentOrCustodian: string | null;
  priority: "critical" | "high" | "medium" | "low";
  relatedQuestion: string | null;
  relatedHypothesis: string | null;
  status: EvidenceRequestStatus;
  requestedDate: string | null;
  receivedDate: string | null;
  deficiency: string | null;
  followUp: string | null;
}

export const EVIDENCE_REQUEST_STATUSES: EvidenceRequestStatus[] = [
  "needed",
  "requested",
  "partially_received",
  "received",
  "unavailable",
  "declined",
  "not_applicable",
];

export function generateEvidenceRequestsFromTemplate(
  template: GovernmentTemplate,
  opts?: { prefix?: string },
): GovernmentEvidenceRequest[] {
  const prefix = opts?.prefix ?? "evr";
  const required = template.requiredEvidenceCategories.map((cat, i) => ({
    id: `${prefix}_req_${i + 1}`,
    requestedRecord: cat.replace(/_/g, " "),
    category: cat,
    reasonNeeded: `Required for ${template.title}`,
    dateRange: null,
    departmentOrCustodian: null,
    priority: "high" as const,
    relatedQuestion: template.defaultQuestions[i % template.defaultQuestions.length] ?? null,
    relatedHypothesis: template.defaultHypotheses[0] ?? null,
    status: "needed" as const,
    requestedDate: null,
    receivedDate: null,
    deficiency: null,
    followUp: null,
  }));
  const optional = template.optionalEvidenceCategories.slice(0, 6).map((cat, i) => ({
    id: `${prefix}_opt_${i + 1}`,
    requestedRecord: cat.replace(/_/g, " "),
    category: cat,
    reasonNeeded: `Optional corroboration for ${template.title}`,
    dateRange: null,
    departmentOrCustodian: null,
    priority: "medium" as const,
    relatedQuestion: template.defaultQuestions[(i + 1) % template.defaultQuestions.length] ?? null,
    relatedHypothesis: template.defaultHypotheses[1] ?? template.defaultHypotheses[0] ?? null,
    status: "needed" as const,
    requestedDate: null,
    receivedDate: null,
    deficiency: null,
    followUp: null,
  }));
  return [...required, ...optional];
}

export function transitionEvidenceRequestStatus(
  current: EvidenceRequestStatus,
  next: EvidenceRequestStatus,
): { ok: boolean; status: EvidenceRequestStatus; error?: string } {
  if (!EVIDENCE_REQUEST_STATUSES.includes(next)) {
    return { ok: false, status: current, error: "invalid status" };
  }
  return { ok: true, status: next };
}
