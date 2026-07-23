/** Executive dashboard transforms (KC-007). */

export interface RecentlyUpdatedItem {
  id: string;
  title: string;
  updatedAt: string;
  kind: "investigation" | "report" | "evidence" | "finding";
}

export interface RecentReportItem {
  id: string;
  title: string;
  status: "draft" | "review" | "published";
  updatedAt: string;
}

export interface PerformanceSummary {
  avgInvestigationDays: number | null;
  evidenceCompletionRate: number | null;
  reviewBacklog: number;
}

export interface PilotScoresSummary {
  totalPilots: number;
  activePilots: number;
  avgScore: number | null;
}

export interface ExecutiveDashboardStats {
  openInvestigations: number;
  completed: number;
  evidenceCount: number;
  pendingEvidence: number;
  highRiskCases: number;
  reviewRequired: number;
  recentlyUpdated: RecentlyUpdatedItem[];
  recentReports: RecentReportItem[];
  performanceSummary: PerformanceSummary;
  pilotScoresSummary: PilotScoresSummary;
}

export interface ExecutiveDashboardInput {
  openInvestigations?: number;
  completed?: number;
  evidenceCount?: number;
  pendingEvidence?: number;
  highRiskCases?: number;
  reviewRequired?: number;
  recentlyUpdated?: RecentlyUpdatedItem[];
  recentReports?: RecentReportItem[];
  performanceSummary?: Partial<PerformanceSummary>;
  pilotScoresSummary?: Partial<PilotScoresSummary>;
}

function clampNonNegative(n: number): number {
  return Number.isFinite(n) && n >= 0 ? n : 0;
}

export function buildExecutiveDashboard(input: ExecutiveDashboardInput): ExecutiveDashboardStats {
  const recentlyUpdated = [...(input.recentlyUpdated ?? [])].sort((a, b) =>
    String(b.updatedAt).localeCompare(String(a.updatedAt)),
  );
  const recentReports = [...(input.recentReports ?? [])].sort((a, b) =>
    String(b.updatedAt).localeCompare(String(a.updatedAt)),
  );

  const perf = input.performanceSummary ?? {};
  const pilot = input.pilotScoresSummary ?? {};

  return {
    openInvestigations: clampNonNegative(input.openInvestigations ?? 0),
    completed: clampNonNegative(input.completed ?? 0),
    evidenceCount: clampNonNegative(input.evidenceCount ?? 0),
    pendingEvidence: clampNonNegative(input.pendingEvidence ?? 0),
    highRiskCases: clampNonNegative(input.highRiskCases ?? 0),
    reviewRequired: clampNonNegative(input.reviewRequired ?? 0),
    recentlyUpdated,
    recentReports,
    performanceSummary: {
      avgInvestigationDays:
        perf.avgInvestigationDays != null && Number.isFinite(perf.avgInvestigationDays)
          ? perf.avgInvestigationDays
          : null,
      evidenceCompletionRate:
        perf.evidenceCompletionRate != null && Number.isFinite(perf.evidenceCompletionRate)
          ? Math.min(100, Math.max(0, perf.evidenceCompletionRate))
          : null,
      reviewBacklog: clampNonNegative(perf.reviewBacklog ?? 0),
    },
    pilotScoresSummary: {
      totalPilots: clampNonNegative(pilot.totalPilots ?? 0),
      activePilots: clampNonNegative(pilot.activePilots ?? 0),
      avgScore:
        pilot.avgScore != null && Number.isFinite(pilot.avgScore) ? pilot.avgScore : null,
    },
  };
}
