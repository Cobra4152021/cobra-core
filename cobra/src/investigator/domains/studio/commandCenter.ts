/** Command center aggregation (KC-007). */

export interface CommandCenterReviewItem {
  id: string;
  title: string;
  kind: "investigation" | "report" | "finding";
  priority: "low" | "medium" | "high";
}

export interface CommandCenterBlockedItem {
  id: string;
  title: string;
  reason: string;
}

export interface CommandCenterEvidenceRequest {
  id: string;
  label: string;
  investigationId: string;
  status: "open" | "fulfilled" | "overdue";
}

export interface CommandCenterFinding {
  id: string;
  summary: string;
  risk: "high" | "medium" | "low";
}

export interface CommandCenterPublication {
  id: string;
  title: string;
  status: "pending_review" | "approved" | "blocked";
}

export interface CommandCenterPilotStatus {
  id: string;
  name: string;
  status: "active" | "paused" | "completed";
  score: number | null;
}

export interface CommandCenterSnapshot {
  reviewNeeded: CommandCenterReviewItem[];
  blocked: CommandCenterBlockedItem[];
  evidenceRequests: CommandCenterEvidenceRequest[];
  highRiskFindings: CommandCenterFinding[];
  pendingPublication: CommandCenterPublication[];
  pilotStatus: CommandCenterPilotStatus[];
  totals: {
    reviewNeeded: number;
    blocked: number;
    evidenceRequests: number;
    highRiskFindings: number;
    pendingPublication: number;
    activePilots: number;
  };
}

export interface CommandCenterInput {
  reviewNeeded?: CommandCenterReviewItem[];
  blocked?: CommandCenterBlockedItem[];
  evidenceRequests?: CommandCenterEvidenceRequest[];
  highRiskFindings?: CommandCenterFinding[];
  pendingPublication?: CommandCenterPublication[];
  pilotStatus?: CommandCenterPilotStatus[];
}

export function buildCommandCenter(input: CommandCenterInput = {}): CommandCenterSnapshot {
  const reviewNeeded = input.reviewNeeded ?? [];
  const blocked = input.blocked ?? [];
  const evidenceRequests = input.evidenceRequests ?? [];
  const highRiskFindings = (input.highRiskFindings ?? []).filter((f) => f.risk === "high");
  const pendingPublication = (input.pendingPublication ?? []).filter(
    (p) => p.status === "pending_review" || p.status === "blocked",
  );
  const pilotStatus = input.pilotStatus ?? [];
  const activePilots = pilotStatus.filter((p) => p.status === "active").length;

  return {
    reviewNeeded,
    blocked,
    evidenceRequests,
    highRiskFindings,
    pendingPublication,
    pilotStatus,
    totals: {
      reviewNeeded: reviewNeeded.length,
      blocked: blocked.length,
      evidenceRequests: evidenceRequests.length,
      highRiskFindings: highRiskFindings.length,
      pendingPublication: pendingPublication.length,
      activePilots,
    },
  };
}
